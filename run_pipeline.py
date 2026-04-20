"""
run_pipeline.py — Full end-to-end procurement pipeline with Gmail monitoring.

Watches your Gmail inbox for new procurement requests, then runs the
complete pipeline: Analysis → ACK → Sourcing → RFQs → Storage → Evaluation.

Usage:
    python run_pipeline.py              # watch Gmail inbox (default)
    python run_pipeline.py --once       # process current unread emails and exit
    python run_pipeline.py --cli        # manual CLI mode (no Gmail, type the email)
"""
import argparse
import imaplib
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)
    from importlib import reload
    import config as _cfg
    reload(_cfg)

from config import settings
from logger import get_logger
from email_gateway.parser import EmailParser
from agents.analysis.agent import AnalysisAgent
from agents.analysis.tools import send_request_acknowledgment

logger = get_logger(__name__)

POLL_INTERVAL = 15  # seconds
MAX_RELAUNCHES = 3  # maximum number of relaunch rounds (B3)
SUPPLIER_REPLY_WAIT_MINUTES = 30  # wait time for supplier replies after RFQs (B2)
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def _store_evals_from_report(request_id: str, report_path: str):
    """
    Fallback: re-read the evaluation JSON output and store evaluations to DB.
    This handles cases where the LLM orchestrator failed to persist evaluations.
    """
    import glob
    import json as _json

    # Find the most recent evaluation JSON
    eval_files = sorted(
        glob.glob(str(OUTPUT_DIR / "evaluation_*.json")),
        key=lambda f: Path(f).stat().st_mtime,
        reverse=True,
    )
    if not eval_files:
        print("  [DB] No evaluation JSON found to recover from")
        return

    with open(eval_files[0], "r", encoding="utf-8") as f:
        eval_data = _json.load(f)

    scores = eval_data.get("scores", [])
    if not scores:
        print("  [DB] Evaluation JSON has no scores")
        return

    from agents.agent_storage.agent import StorageAgent
    storage = StorageAgent()
    storage.store_evaluations(request_id, scores, report_path)
    print(f"  [DB] {len(scores)} evaluation(s) recovered and stored")


def print_banner():
    print("\n" + "=" * 60)
    print("  PROCUREMENT PIPELINE — FULL E2E MODE")
    print("=" * 60)


def print_result(result):
    print("\n" + "=" * 60)
    print("  PIPELINE RESULT")
    print("=" * 60)
    print(f"  Status:          {result.status}")
    print(f"  Product:         {result.product}")
    print(f"  Request ID:      {result.request_id}")
    print(f"  Suppliers found: {result.suppliers_found}")
    print(f"  RFQs sent:       {result.rfqs_sent}")
    print(f"  Offers received: {result.offers_received}")
    print(f"  Best offer:      {result.best_offer}")
    print(f"  Report path:     {result.report_path}")
    print(f"  Error:           {result.error}")
    print(f"  Timestamp:       {result.timestamp}")
    print("=" * 60 + "\n")


def send_report_to_requester(requester_email: str, product: str, report_path: str, best_offer: str, request_id: str = None):
    """Send the evaluation PDF to the requester and ask for their decision."""
    from email_gateway.sender import EmailSender

    dashboard_url = os.environ.get("DASHBOARD_URL", "https://procurement-ai.click")
    select_link = f"\n📊 View Report & Select Supplier:\n{dashboard_url}/select/{request_id}\n\n" if request_id else "\n"

    subject = f"Evaluation Report — {product}"
    body = (
        "Hello,\n\n"
        f"Your supplier evaluation report for \"{product}\" is ready.\n\n"
        f"Our recommendation is: {best_offer}\n"
        f"{select_link}"
        "You can:\n"
        "• Click the link above to view detailed comparisons and place your order\n"
        "• Reply \"RELAUNCH\" to this email for a new search\n\n"
        "Please find the detailed PDF report attached.\n\n"
        "Regards,\nProcurement AI Team"
    )

    sender = EmailSender()
    message_id = sender.send(
        to_email=requester_email,
        subject=subject,
        body=body,
        attachment_path=report_path,
    )
    logger.info("Report sent to requester", extra={"to": requester_email, "message_id": message_id})
    return message_id


def wait_for_requester_decision(conn, requester_email: str, product: str, timeout_minutes: int = 60):
    """
    Poll inbox for the requester's relaunch reply.
    Returns: "relaunch" | "timeout"
    Only triggers on RELAUNCH — if the requester is satisfied, they don't reply.
    """
    import email as email_lib

    print(f"\n  Waiting for requester decision (timeout: {timeout_minutes} min)...")
    print(f"  Checking every {POLL_INTERVAL}s for reply from {requester_email}\n")

    start = time.time()
    while (time.time() - start) < timeout_minutes * 60:
        try:
            conn.select("INBOX")
            _, msg_nums = conn.search(None, "UNSEEN")
            ids = msg_nums[0].split()

            for num in ids:
                _, data = conn.fetch(num, "(RFC822)")
                raw = data[0][1]
                msg = email_lib.message_from_bytes(raw)

                from_addr = msg.get("From", "")
                # Check if it's from the requester
                if requester_email.lower() not in from_addr.lower():
                    continue

                conn.store(num, "+FLAGS", "\\Seen")

                # Extract body
                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body_text = payload.decode("utf-8", errors="replace")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode("utf-8", errors="replace")

                decision = body_text.strip().lower()
                print(f"  Reply received: {body_text.strip()[:100]!r}")

                if any(w in decision for w in ["relaunch", "relancer", "retry", "autre", "non", "no"]):
                    return "relaunch"
                # Any other reply is ignored (requester handles it themselves)

        except imaplib.IMAP4.abort:
            conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
            password = settings.gmail_app_password.split("#", 1)[0].replace(" ", "").strip()
            conn.login(settings.gmail_address, password)

        now = datetime.now().strftime("%H:%M:%S")
        print(f"  [{now}] No decision yet — checking again in {POLL_INTERVAL}s")
        time.sleep(POLL_INTERVAL)

    return "timeout"


def _wait_and_recheck_offers(imap_conn, initial_result, spec, requester, attachment_text, excluded_suppliers):
    """
    B2: Poll inbox for supplier replies, then re-run evaluation if offers arrive.
    Returns an updated PipelineResult (or the original if no offers come in).
    """
    import json
    from dataclasses import asdict
    from agents.agent_communication.agent import CommunicationAgent
    from agents.agent_evaluation.agent import EvaluationAgent

    product = spec.product if hasattr(spec, "product") else spec.get("product", "")
    spec_dict = asdict(spec) if hasattr(spec, "__dataclass_fields__") else spec

    start = time.time()
    timeout = SUPPLIER_REPLY_WAIT_MINUTES * 60

    comm_agent = CommunicationAgent()
    check_interval = 30  # check every 30 seconds

    while (time.time() - start) < timeout:
        now = datetime.now().strftime("%H:%M:%S")
        elapsed = int((time.time() - start) / 60)
        print(f"  [{now}] Waiting for supplier replies... ({elapsed}/{SUPPLIER_REPLY_WAIT_MINUTES} min)")
        time.sleep(check_interval)

        # Check for new replies directly via IMAP
        from agents.agent_communication.tools import fetch_supplier_replies
        rfq_subject = f"RFQ — {product}"
        raw_replies = json.loads(fetch_supplier_replies(rfq_subject))

        if raw_replies:
            # Parse raw replies into offers via the communication agent
            dummy_rfqs = [{"supplier_email": r.get("from_email", ""), "status": "sent"} for r in raw_replies]
            offers = comm_agent.check_responses(dummy_rfqs, product)
        else:
            offers = []

        if offers:
            print(f"\n  {len(offers)} supplier reply(ies) received! Running evaluation...")
            eval_agent = EvaluationAgent()
            offer_dicts = []
            for o in offers:
                if hasattr(o, "__dataclass_fields__"):
                    offer_dicts.append(asdict(o))
                else:
                    offer_dicts.append(o)

            eval_result = eval_agent.evaluate(offer_dicts, spec_dict)

            # ── Persist offers + evaluations + update status in DB ──
            request_id = initial_result.request_id
            if request_id:
                try:
                    from agents.agent_storage.agent import StorageAgent
                    from db.models import Supplier as SupplierModel, RFQ as RFQModel, get_session_factory
                    import uuid as _uuid
                    storage = StorageAgent()

                    # Build supplier_map and rfq_map from DB
                    _S = get_session_factory()
                    supplier_map = {}
                    rfq_map = {}
                    with _S() as _sess:
                        _rid = _uuid.UUID(request_id) if isinstance(request_id, str) else request_id
                        for sup in _sess.query(SupplierModel).filter_by(request_id=_rid).all():
                            if sup.email:
                                supplier_map[sup.email] = str(sup.id)
                        for rfq in _sess.query(RFQModel).filter_by(request_id=_rid).all():
                            sup = _sess.query(SupplierModel).filter_by(id=rfq.supplier_id).first()
                            if sup and sup.email:
                                rfq_map[sup.email] = str(rfq.id)
                    print(f"  [DB] Maps: suppliers={supplier_map}, rfqs={rfq_map}")

                    # Store offers
                    storage.store_offers(request_id, offer_dicts, supplier_map, rfq_map)
                    print(f"  [DB] {len(offer_dicts)} offer(s) stored")

                    # Store evaluation scores
                    scores = getattr(eval_result, "scores", None) or getattr(eval_result, "ranking", None) or []
                    print(f"  [DB] eval_result type={type(eval_result).__name__}, scores count={len(scores)}")
                    if scores:
                        score_dicts = []
                        for s in scores:
                            score_dicts.append(asdict(s) if hasattr(s, "__dataclass_fields__") else s)
                        report_path = getattr(eval_result, "report_path", None)
                        req_id_str = str(request_id) if not isinstance(request_id, str) else request_id
                        storage.store_evaluations(req_id_str, score_dicts, report_path)
                        print(f"  [DB] {len(score_dicts)} evaluation(s) stored")
                    else:
                        print(f"  [DB] WARNING: No scores in eval_result! attrs={dir(eval_result)}")

                    # Update request status to evaluation_sent
                    from db.models import ProcurementRequest, get_session_factory
                    Session = get_session_factory()
                    with Session() as session:
                        req = session.query(ProcurementRequest).filter_by(id=request_id).first()
                        if req:
                            req.status = "evaluation_sent"
                            session.commit()
                            print("  [DB] Request status updated to 'evaluation_sent'")
                except Exception as e:
                    print(f"  [DB] Warning: could not persist B2 results: {e}")

            from agents.orchestrator.agent import PipelineResult
            return PipelineResult(
                request_id=request_id,
                product=product,
                status="completed",
                suppliers_found=initial_result.suppliers_found,
                rfqs_sent=initial_result.rfqs_sent,
                offers_received=len(offers),
                best_offer=getattr(eval_result, "best_offer", None),
                report_path=getattr(eval_result, "report_path", None),
                error=None,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    print(f"\n  No supplier replies after {SUPPLIER_REPLY_WAIT_MINUTES} min — continuing with no offers.")
    return initial_result


def process_email(raw_bytes: bytes, analysis_agent: AnalysisAgent, imap_conn=None):
    """Process a single incoming email through the full pipeline."""
    import json
    from agents.orchestrator import Orchestrator

    parser = EmailParser()
    parsed = parser.parse(raw_bytes)

    print(f"\n{'=' * 60}")
    print(f"  NEW EMAIL — {datetime.now().strftime('%H:%M:%S')}")
    print(f"    From    : {parsed.from_email}")
    print(f"    Subject : {parsed.subject}")
    print(f"    Body    : {parsed.body[:200].strip()!r}")
    print(f"{'=' * 60}")

    # ── Collect attachment text (PDF, Excel, images) ────────────
    attachment_text = ""
    if parsed.attachments:
        att_parts = []
        for att in parsed.attachments:
            if att.get("text", "").strip():
                att_parts.append(f"[{att['filename']}]\n{att['text']}")
        if att_parts:
            attachment_text = "\n\n".join(att_parts)
            print(f"  Attachments with text: {len(att_parts)}")

    # ── Step 1: Analysis (Agent 1) ───────────────────────────────
    print("\n[Agent 1 — Analysis] Analyzing procurement request...")
    spec = analysis_agent.analyze(parsed.body, parsed.from_email, attachment_text=attachment_text)

    if spec.is_valid:
        print("  Valid request!")
        print(f"    Product  : {spec.product}")
        print(f"    Category : {spec.category}")
        print(f"    Quantity : {spec.quantity} {spec.unit or ''}")
        print(f"    Budget   : {spec.budget_min or 'N/A'} - {spec.budget_max or 'N/A'} TND")
        print(f"    Deadline : {spec.deadline or 'Not specified'}")
    else:
        print(f"  Request rejected: {spec.rejection_reason}")

    # ── Step 1b: Send ACK email to requester ─────────────────────
    print("\n[Agent 1 — ACK] Sending acknowledgment email...")
    try:
        send_request_acknowledgment(
            requester_email=spec.requester_email or parsed.from_email,
            is_valid=spec.is_valid,
            product=spec.product,
        )
        print(f"  ACK sent to {spec.requester_email or parsed.from_email}")
    except Exception as exc:
        print(f"  ACK failed: {exc}")

    # Save analysis result
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = "valid" if spec.is_valid else "rejected"
    analysis_path = OUTPUT_DIR / f"analysis_{label}_{ts}.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(asdict(spec), f, ensure_ascii=False, indent=2, default=str)
    print(f"  Analysis saved: {analysis_path}")

    if not spec.is_valid:
        print("\n  Pipeline stopped — request was rejected.")
        return

    # ── Steps 2-5: Run via Orchestrator ──────────────────────────
    excluded_suppliers = []
    relaunch_count = 0
    requester = spec.requester_email or parsed.from_email

    while True:
        if relaunch_count > 0:
            print(f"\n  [Relaunch {relaunch_count}/{MAX_RELAUNCHES}] Excluded suppliers: {excluded_suppliers}")

        print("\n[Orchestrator] Launching pipeline (Sourcing → RFQs → Storage → Evaluation)...")
        orchestrator = Orchestrator()
        result = orchestrator.run(
            parsed.body, requester,
            procurement_spec=asdict(spec),
            attachment_text=attachment_text,
            excluded_suppliers=excluded_suppliers,
        )

        # ── B2: Wait for supplier replies if none received yet ──
        # Check actual DB state — don't trust LLM's offers_received count
        actual_offers = 0
        actual_evals = 0
        if result.request_id:
            try:
                from db.models import Offer as OfferModel, Evaluation as EvalModel, get_session_factory
                _S = get_session_factory()
                with _S() as _sess:
                    import uuid as _uuid
                    _rid = _uuid.UUID(result.request_id)
                    actual_offers = _sess.query(OfferModel).filter_by(request_id=_rid).count()
                    actual_evals = _sess.query(EvalModel).filter_by(request_id=_rid).count()
            except Exception:
                pass

        needs_wait = (
            result.status == "awaiting_responses"
            or (actual_offers == 0 and actual_evals == 0
                and result.status not in ("rejected", "failed")
                and result.product)  # has a valid product = RFQs were likely sent
        )
        print(f"\n  [DEBUG] status={result.status} rfqs_sent={result.rfqs_sent} "
              f"offers_in_db={actual_offers} evals_in_db={actual_evals} needs_wait={needs_wait} "
              f"imap={'yes' if imap_conn else 'no'}")
        if needs_wait and imap_conn is not None:
            print(f"\n[Wait] No immediate replies — waiting up to {SUPPLIER_REPLY_WAIT_MINUTES} min for supplier responses...")
            result = _wait_and_recheck_offers(
                imap_conn, result, spec, requester, attachment_text, excluded_suppliers,
            )

        # ── Post-pipeline: ensure evaluations are persisted & status updated ──
        if result.request_id and result.status == "completed":
            try:
                from db.models import Evaluation as EvalModel, Offer as OfferModel, Supplier as SupplierModel
                from db.models import ProcurementRequest, get_session_factory
                from agents.agent_storage.agent import StorageAgent
                import uuid as _uuid
                _S = get_session_factory()
                with _S() as _sess:
                    _rid = _uuid.UUID(result.request_id)
                    eval_count = _sess.query(EvalModel).filter_by(request_id=_rid).count()
                    if eval_count == 0:
                        print("  [DB] Evaluations missing — attempting recovery...")
                        # Try 1: recover from evaluation JSON file
                        if result.report_path:
                            _store_evals_from_report(result.request_id, result.report_path)
                            eval_count = _sess.query(EvalModel).filter_by(request_id=_rid).count()

                        # Try 2: if still no evals, re-run evaluation on DB offers
                        if eval_count == 0:
                            offers_db = _sess.query(OfferModel).filter_by(request_id=_rid).all()
                            if offers_db:
                                print(f"  [DB] Re-running evaluation on {len(offers_db)} offer(s)...")
                                from dataclasses import asdict as _asdict
                                from agents.agent_evaluation.agent import EvaluationAgent
                                offer_dicts = []
                                for o in offers_db:
                                    sup = _sess.query(SupplierModel).filter_by(id=o.supplier_id).first()
                                    offer_dicts.append({
                                        "supplier_name": sup.name if sup else "Unknown",
                                        "supplier_email": sup.email if sup else "",
                                        "unit_price": o.unit_price,
                                        "total_price": o.total_price,
                                        "currency": o.currency or "TND",
                                        "delivery_days": o.delivery_days,
                                        "warranty": o.warranty,
                                        "payment_terms": o.payment_terms,
                                        "notes": o.notes,
                                    })
                                req_obj = _sess.query(ProcurementRequest).filter_by(id=_rid).first()
                                spec_dict = {
                                    "product": req_obj.product if req_obj else result.product,
                                    "quantity": req_obj.quantity if req_obj else None,
                                    "budget_min": req_obj.budget_min if req_obj else None,
                                    "budget_max": req_obj.budget_max if req_obj else None,
                                }
                                eval_agent = EvaluationAgent()
                                eval_res = eval_agent.evaluate(offer_dicts, spec_dict)
                                scores = getattr(eval_res, "scores", []) or getattr(eval_res, "ranking", [])
                                if scores:
                                    score_dicts = [_asdict(s) if hasattr(s, "__dataclass_fields__") else s for s in scores]
                                    storage = StorageAgent()
                                    storage.store_evaluations(result.request_id, score_dicts, getattr(eval_res, "report_path", None))
                                    print(f"  [DB] {len(score_dicts)} evaluation(s) stored via re-evaluation")

                    # Update status to evaluation_sent
                    req_obj = _sess.query(ProcurementRequest).filter_by(id=_rid).first()
                    if req_obj and req_obj.status not in ("evaluation_sent", "po_generated", "delivered"):
                        req_obj.status = "evaluation_sent"
                        _sess.commit()
                        print("  [DB] Request status updated to 'evaluation_sent'")
            except Exception as exc:
                import traceback
                print(f"  [DB] Warning: post-pipeline sync failed: {exc}")
                traceback.print_exc()

        print_result(result)

        # If no report was generated, stop
        if not result.report_path or result.status != "completed":
            print("  No evaluation report — pipeline ended.")
            break

        # ── Send PDF report to requester ─────────────────────────
        print("[Decision] Sending evaluation report to requester...")
        try:
            send_report_to_requester(
                requester_email=requester,
                product=result.product,
                report_path=result.report_path,
                best_offer=result.best_offer or "N/A",
                request_id=result.request_id,
            )
            print(f"  Report sent to {requester}")
        except Exception as exc:
            print(f"  Failed to send report: {exc}")
            break

        # ── Wait for requester's decision ────────────────────────
        if imap_conn is None:
            print("\n  (No IMAP connection — skipping decision wait in CLI mode)")
            break

        decision = wait_for_requester_decision(
            imap_conn, requester, result.product,
        )

        if decision == "relaunch":
            relaunch_count += 1
            if relaunch_count >= MAX_RELAUNCHES:
                print(f"\n  Max relaunches reached ({MAX_RELAUNCHES}) — pipeline complete.")
                break
            print("\n  Decision: RELAUNCH — searching for new suppliers...")
            excluded_suppliers.append(result.best_offer)
            continue
        else:  # timeout — requester is satisfied or didn't reply
            print("\n  No relaunch requested — pipeline complete.")
            break


def run_gmail_watch(once: bool = False):
    """Watch Gmail inbox for new procurement request emails."""
    print_banner()
    print(f"  Gmail     : {settings.gmail_address}")
    print(f"  Interval  : every {POLL_INTERVAL}s")
    print(f"  Mode      : {'single pass' if once else 'continuous (Ctrl+C to stop)'}")
    print()

    if not settings.gmail_address or not settings.gmail_app_password:
        print("ERROR: GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env")
        sys.exit(1)

    password = settings.gmail_app_password.split("#", 1)[0].replace(" ", "").strip()
    analysis_agent = AnalysisAgent()

    def poll_once(conn):
        conn.select("INBOX")
        _, msg_nums = conn.search(None, "UNSEEN")
        ids = msg_nums[0].split()

        if not ids or ids == [b""]:
            return 0

        for num in ids:
            _, data = conn.fetch(num, "(RFC822)")
            raw = data[0][1]
            conn.store(num, "+FLAGS", "\\Seen")
            try:
                process_email(raw, analysis_agent, imap_conn=conn)
            except Exception as exc:
                print(f"\n  ERROR processing email: {exc}")
                logger.error("Pipeline error", extra={"error": str(exc)})

        return len(ids)

    conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    conn.login(settings.gmail_address, password)
    print("  Connected to Gmail — watching inbox...\n")

    if once:
        n = poll_once(conn)
        print(f"\n  Processed {n} email(s).")
        conn.logout()
        return

    try:
        while True:
            try:
                n = poll_once(conn)
                if n == 0:
                    now = datetime.now().strftime("%H:%M:%S")
                    print(f"  [{now}] No new emails — next check in {POLL_INTERVAL}s")
            except imaplib.IMAP4.abort:
                print("  IMAP connection lost — reconnecting...")
                conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
                conn.login(settings.gmail_address, password)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n  Stopped.")
        conn.logout()


def run_cli_mode():
    """Manual CLI mode — type the email body directly."""
    print_banner()
    print("  Mode: CLI (manual input)\n")

    requester = input("  Requester email: ").strip() or "test@company.com"
    print("  Enter the procurement request (end with empty line):")
    lines = []
    while True:
        line = input("  > ")
        if line == "":
            break
        lines.append(line)
    email_body = "\n".join(lines)

    if not email_body.strip():
        print("  Error: empty email body")
        sys.exit(1)

    from agents.orchestrator import Orchestrator
    print(f"\n  Running pipeline for: {requester}\n")
    orchestrator = Orchestrator()
    result = orchestrator.run(email_body, requester)

    # ── B2: Wait for supplier replies if status is awaiting_responses ──
    if result.status == "awaiting_responses":
        print(f"\n[Wait] No immediate replies — waiting up to {SUPPLIER_REPLY_WAIT_MINUTES} min for supplier responses...")
        print("       (Reply to the RFQ email from your supplier mailbox, then sit back)\n")

        # Open an IMAP connection for polling
        imap_conn = None
        try:
            imap_conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
            password = settings.gmail_app_password.replace(" ", "")
            imap_conn.login(settings.gmail_address, password)
        except Exception as e:
            print(f"  Warning: could not open IMAP for reply polling: {e}")

        if imap_conn:
            spec_dict = {"product": result.product}
            result = _wait_and_recheck_offers(
                imap_conn, result, spec_dict, requester, "", [],
            )
            try:
                imap_conn.logout()
            except Exception:
                pass

    # ── Post-pipeline: ensure evaluations are persisted ──
    if result.request_id and result.status == "completed":
        try:
            from db.models import Evaluation as EvalModel, Offer as OfferModel, Supplier as SupplierModel
            from db.models import ProcurementRequest, get_session_factory
            from agents.agent_storage.agent import StorageAgent
            import uuid as _uuid
            _S = get_session_factory()
            with _S() as _sess:
                _rid = _uuid.UUID(result.request_id)
                eval_count = _sess.query(EvalModel).filter_by(request_id=_rid).count()
                if eval_count == 0 and result.report_path:
                    _store_evals_from_report(result.request_id, result.report_path)
                    eval_count = _sess.query(EvalModel).filter_by(request_id=_rid).count()
                if eval_count == 0:
                    offers_db = _sess.query(OfferModel).filter_by(request_id=_rid).all()
                    if offers_db:
                        print(f"  [DB] Re-running evaluation on {len(offers_db)} offer(s)...")
                        from agents.agent_evaluation.agent import EvaluationAgent
                        from dataclasses import asdict as _asdict
                        offer_dicts = []
                        for o in offers_db:
                            sup = _sess.query(SupplierModel).filter_by(id=o.supplier_id).first()
                            offer_dicts.append({
                                "supplier_name": sup.name if sup else "Unknown",
                                "supplier_email": sup.email if sup else "",
                                "unit_price": o.unit_price, "total_price": o.total_price,
                                "currency": o.currency or "TND", "delivery_days": o.delivery_days,
                                "warranty": o.warranty, "payment_terms": o.payment_terms,
                            })
                        req_obj = _sess.query(ProcurementRequest).filter_by(id=_rid).first()
                        spec_d = {"product": req_obj.product if req_obj else result.product,
                                  "quantity": req_obj.quantity if req_obj else None,
                                  "budget_min": req_obj.budget_min if req_obj else None,
                                  "budget_max": req_obj.budget_max if req_obj else None}
                        eval_agent_cli = EvaluationAgent()
                        eval_res = eval_agent_cli.evaluate(offer_dicts, spec_d)
                        scores = getattr(eval_res, "scores", []) or []
                        if scores:
                            sd = [_asdict(s) if hasattr(s, "__dataclass_fields__") else s for s in scores]
                            StorageAgent().store_evaluations(result.request_id, sd, getattr(eval_res, "report_path", None))
                            print(f"  [DB] {len(sd)} evaluation(s) stored")
                            if not result.report_path:
                                result = result._replace(report_path=getattr(eval_res, "report_path", None)) if hasattr(result, "_replace") else result
                req_obj = _sess.query(ProcurementRequest).filter_by(id=_rid).first()
                if req_obj and req_obj.status not in ("evaluation_sent", "po_generated", "delivered"):
                    req_obj.status = "evaluation_sent"
                    _sess.commit()
        except Exception as exc:
            print(f"  [DB] Warning: post-pipeline sync failed: {exc}")

    print_result(result)

    # ── Send PDF report to requester ─────────────────────────
    if result.report_path and result.status == "completed":
        print("[Decision] Sending evaluation report to requester...")
        try:
            send_report_to_requester(
                requester_email=requester,
                product=result.product,
                report_path=result.report_path,
                best_offer=result.best_offer or "N/A",
                request_id=result.request_id,
            )
            print(f"  Report sent to {requester}")
        except Exception as exc:
            print(f"  Failed to send report: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Procurement Pipeline — Full E2E")
    parser.add_argument("--once", action="store_true",
                        help="Process current unread emails and exit")
    parser.add_argument("--cli", action="store_true",
                        help="Manual CLI mode (no Gmail, type the email)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do NOT send real RFQ emails to suppliers (safe testing)")
    parser.add_argument("--test-supplier", type=str, default=None,
                        help="Inject a test supplier email, skip Tavily sourcing (e.g. --test-supplier you@gmail.com)")
    parser.add_argument("--wait-minutes", type=int, default=None,
                        help="Override supplier reply wait time in minutes (default: 30)")
    args = parser.parse_args()

    if args.dry_run:
        import agents.agent_communication.tools as comm_tools
        comm_tools.DRY_RUN = True
        print("  [DRY-RUN] RFQ emails will NOT be sent to real suppliers.\n")

    if args.test_supplier:
        import agents.orchestrator.tools as orch_tools
        orch_tools.TEST_SUPPLIER = {
            "name": "Test Supplier",
            "email": args.test_supplier,
            "website": None,
            "country": "Tunisia",
            "category": "test",
            "relevance_score": 1.0,
            "source_url": None,
        }
        print(f"  [TEST] Sourcing bypassed — RFQ will be sent to: {args.test_supplier}\n")

    if args.wait_minutes is not None:
        global SUPPLIER_REPLY_WAIT_MINUTES
        SUPPLIER_REPLY_WAIT_MINUTES = args.wait_minutes
        print(f"  [CONFIG] Supplier reply wait time: {args.wait_minutes} min\n")

    if args.cli:
        run_cli_mode()
    else:
        run_gmail_watch(once=args.once)


if __name__ == "__main__":
    main()
