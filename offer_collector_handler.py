"""
offer_collector_handler.py
Lambda triggered by EventBridge every 15 minutes.

Responsibilities:
  1. Query DB for all requests with status='awaiting_responses'
  2. For each request, poll Gmail IMAP for new supplier replies
     (only emails received AFTER the RFQ was sent)
  3. Send reminders to suppliers who haven't replied after 72h
  4. Store new offers to DB
  5. Once EVALUATION_DEADLINE_DAYS have passed since first RFQ sent:
       → run Evaluation on ALL collected offers → send report to requester
       → Update request status to 'completed'
"""
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Make project modules importable ───────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("OUTPUTS_DIR", "/tmp/outputs")

# How many days to wait before running final evaluation
EVALUATION_DEADLINE_DAYS = int(os.environ.get("EVALUATION_DEADLINE_DAYS", "5"))
# Hours before sending a reminder to a non-responding supplier
REMINDER_AFTER_HOURS = int(os.environ.get("REMINDER_AFTER_HOURS", "72"))

from logger import get_logger
from agents.agent_storage.agent import StorageAgent
from agents.agent_communication.agent import CommunicationAgent
from agents.agent_evaluation.agent import EvaluationAgent
from email_gateway.sender import EmailSender

logger = get_logger(__name__)

# ── Singletons ────────────────────────────────────────────────────────────────
_storage = StorageAgent()
_communication = CommunicationAgent()
_evaluation = EvaluationAgent()


def handler(event, context):
    """
    EventBridge scheduled handler — collect supplier offers, send reminders, evaluate.
    """
    logger.info("Offer collector triggered")

    try:
        pending = _storage._tools.get_pending_requests()
    except Exception as exc:
        logger.error("Failed to fetch pending requests", extra={"error": str(exc)})
        return {"statusCode": 500, "body": str(exc)}

    if not pending:
        logger.info("No pending requests — nothing to do")
        return {"statusCode": 200, "body": "no_pending_requests"}

    logger.info(f"Found {len(pending)} pending request(s)")
    results = []

    for req in pending:
        result = _process_pending_request(req)
        results.append(result)

    return {
        "statusCode": 200,
        "body": json.dumps(results, ensure_ascii=False, default=str),
    }


def _process_pending_request(req: dict) -> dict:
    """
    For one pending request:
    - Send reminders to non-responding suppliers after 72h
    - Poll IMAP for new offers
    - Once evaluation deadline (5 days) is reached, evaluate all offers and close
    """
    request_id = req["id"]
    product = req["product"]
    requester_email = req["requester_email"]
    now = datetime.now(timezone.utc)

    logger.info("Processing pending request", extra={
        "request_id": request_id, "product": product,
    })

    rfqs = req.get("rfqs", [])
    sent_rfqs = [r for r in rfqs if r.get("status") == "sent"]

    if not sent_rfqs:
        logger.info("No sent RFQs for this request", extra={"request_id": request_id})
        return {"request_id": request_id, "status": "skipped", "reason": "no_sent_rfqs"}

    # ── Find earliest RFQ sent_at ──────────────────────────────────────────
    sent_at_times = []
    for r in sent_rfqs:
        if r.get("sent_at"):
            try:
                dt = datetime.fromisoformat(r["sent_at"].replace("Z", "+00:00"))
                sent_at_times.append(dt)
            except Exception:
                pass

    earliest_sent_at = min(sent_at_times) if sent_at_times else now
    received_after = earliest_sent_at.isoformat()

    # ── Evaluation deadline: EVALUATION_DEADLINE_DAYS after first RFQ ────
    evaluation_deadline = earliest_sent_at + timedelta(days=EVALUATION_DEADLINE_DAYS)
    deadline_reached = now >= evaluation_deadline

    # ── Get supplier info from DB ──────────────────────────────────────────
    try:
        suppliers_in_db = _storage._tools.get_suppliers_for_request(request_id)
        supplier_map = {s["email"]: s["id"] for s in suppliers_in_db if s.get("email")}
        # Build rfq_map: supplier_email -> rfq_id (cross-ref sent_rfqs with suppliers)
        supplier_id_to_email = {s["id"]: s["email"] for s in suppliers_in_db if s.get("email")}
        rfq_map = {}
        for r in sent_rfqs:
            sup_id = r.get("supplier_id")
            rfq_id = r.get("id")
            if sup_id and rfq_id:
                email = supplier_id_to_email.get(sup_id) or supplier_id_to_email.get(str(sup_id))
                if email:
                    rfq_map[email] = rfq_id
    except Exception as exc:
        logger.error("Failed to get suppliers", extra={"error": str(exc)})
        suppliers_in_db = []
        supplier_map = {}
        rfq_map = {}

    # ── Send reminders to non-responding suppliers (after REMINDER_AFTER_HOURS) ──
    _send_reminders_if_needed(sent_rfqs, suppliers_in_db, product, now)

    # ── Poll IMAP for new replies ──────────────────────────────────────────
    try:
        new_offers = _communication.check_responses(
            rfq_records=sent_rfqs,
            product=product,
            received_after=received_after,
        )
    except Exception as exc:
        logger.error("IMAP check failed", extra={"error": str(exc), "request_id": request_id})
        return {"request_id": request_id, "status": "error", "reason": str(exc)}

    # ── Store newly found offers ───────────────────────────────────────────
    if new_offers:
        logger.info(f"Found {len(new_offers)} new offer(s)", extra={"request_id": request_id})
        try:
            offers_as_dicts = [asdict(o) if hasattr(o, "__dataclass_fields__") else o for o in new_offers]
            _storage._tools.store_offers(request_id, offers_as_dicts, supplier_map, rfq_map=rfq_map)
            logger.info("New offers stored to DB", extra={"request_id": request_id})
        except Exception as exc:
            logger.warning("Failed to store offers", extra={"error": str(exc)})

    # ── Decide whether to evaluate ────────────────────────────────────────
    if not deadline_reached and not new_offers:
        days_left = (evaluation_deadline - now).days
        logger.info("Still waiting for offers", extra={
            "request_id": request_id,
            "days_until_deadline": days_left,
        })
        return {
            "request_id": request_id,
            "status": "still_waiting",
            "new_offers": 0,
            "days_until_deadline": days_left,
        }

    if not deadline_reached:
        # Offers received but deadline not yet reached — store and keep waiting
        logger.info("New offers stored, waiting for deadline before evaluating", extra={
            "request_id": request_id,
            "days_until_deadline": (evaluation_deadline - now).days,
        })
        return {
            "request_id": request_id,
            "status": "offers_collecting",
            "new_offers": len(new_offers),
            "days_until_deadline": (evaluation_deadline - now).days,
        }

    # ── Deadline reached — fetch ALL stored offers and evaluate ───────────
    logger.info("Evaluation deadline reached — running final evaluation", extra={
        "request_id": request_id,
    })

    try:
        all_offers = _storage._tools.get_offers_for_request(request_id)
    except Exception as exc:
        logger.error("Failed to fetch stored offers", extra={"error": str(exc)})
        all_offers = []

    if not all_offers:
        # If deadline is 0 (test mode), don't close — just wait for offers
        if EVALUATION_DEADLINE_DAYS == 0:
            logger.info("Test mode (deadline=0): no offers yet, still waiting", extra={
                "request_id": request_id,
            })
            return {"request_id": request_id, "status": "still_waiting", "new_offers": 0}
        logger.warning("Deadline reached but no offers received — closing request", extra={
            "request_id": request_id,
        })
        _storage._tools.update_request_status(request_id, "completed")
        _send_no_offer_notification(requester_email, product)
        return {
            "request_id": request_id,
            "status": "completed",
            "reason": "deadline_reached_no_offers",
        }

    # ── Run Evaluation on ALL offers ──────────────────────────────────────
    spec = {
        "product": req.get("product", ""),
        "category": req.get("category", ""),
        "quantity": req.get("quantity"),
        "unit": req.get("unit"),
        "budget_min": req.get("budget_min"),
        "budget_max": req.get("budget_max"),
        "deadline": req.get("deadline"),
        "requester_email": requester_email,
    }
    try:
        eval_result = _evaluation.evaluate(offers=all_offers, procurement_spec=spec)
        logger.info("Evaluation complete", extra={
            "best": eval_result.best_offer,
            "offers_evaluated": len(eval_result.scores),
        })
    except Exception as exc:
        logger.error("Evaluation failed", extra={"error": str(exc)})
        eval_result = None

    # ── Send evaluation report to requester ───────────────────────────────
    if eval_result and requester_email:
        try:
            _send_evaluation_report(requester_email, product, eval_result, len(all_offers))
        except Exception as exc:
            logger.warning("Failed to send evaluation report", extra={"error": str(exc)})

    # ── Mark request completed ────────────────────────────────────────────
    try:
        _storage._tools.update_request_status(request_id, "completed")
        logger.info("Request marked completed", extra={"request_id": request_id})
    except Exception as exc:
        logger.warning("Failed to update status", extra={"error": str(exc)})

    return {
        "request_id": request_id,
        "status": "completed",
        "total_offers_evaluated": len(all_offers),
        "best_offer": eval_result.best_offer if eval_result else None,
    }


def _send_reminders_if_needed(sent_rfqs: list, suppliers_in_db: list, product: str, now: datetime) -> None:
    """
    For each RFQ sent more than REMINDER_AFTER_HOURS ago without a reminder yet,
    send a follow-up email to the supplier.
    """
    reminder_threshold = now - timedelta(hours=REMINDER_AFTER_HOURS)
    supplier_id_to_email = {s["id"]: s["email"] for s in suppliers_in_db if s.get("email")}
    supplier_id_to_name = {s["id"]: s["name"] for s in suppliers_in_db if s.get("name")}

    sender = EmailSender()

    for rfq in sent_rfqs:
        if rfq.get("reminder_sent"):
            continue

        sent_at_str = rfq.get("sent_at")
        if not sent_at_str:
            continue

        try:
            sent_at = datetime.fromisoformat(sent_at_str.replace("Z", "+00:00"))
        except Exception:
            continue

        if sent_at > reminder_threshold:
            continue  # Not 72h yet

        supplier_id = rfq.get("supplier_id")
        supplier_email = supplier_id_to_email.get(supplier_id)
        supplier_name = supplier_id_to_name.get(supplier_id, "Fournisseur")
        rfq_subject = rfq.get("subject", f"RFQ — {product}")
        rfq_id = rfq.get("id")

        if not supplier_email:
            continue

        body = (
            f"Bonjour {supplier_name},\n\n"
            f"Nous nous permettons de vous relancer concernant notre appel d'offres pour : {product}.\n\n"
            f"Nous n'avons pas encore reçu votre réponse. Pourriez-vous nous faire parvenir "
            f"votre offre dans les meilleurs délais ?\n\n"
            f"Référence : {rfq_subject}\n\n"
            f"Cordialement,\n"
            f"Procurement AI System"
        )

        try:
            sender.send(
                to_email=supplier_email,
                subject=f"Relance — {rfq_subject}",
                body=body,
            )
            _storage._tools.mark_reminder_sent(rfq_id)
            logger.info("Reminder sent", extra={"supplier": supplier_email, "product": product})
        except Exception as exc:
            logger.warning("Failed to send reminder", extra={"error": str(exc), "supplier": supplier_email})


def _send_evaluation_report(requester_email: str, product: str, eval_result, total_offers: int) -> None:
    """Email the final evaluation summary to the requester."""
    if not eval_result.scores:
        return

    lines = [
        "Bonjour,",
        "",
        f"L'évaluation finale des offres pour votre demande de : {product} est terminée.",
        f"Nombre total d'offres reçues : {total_offers}",
        "",
        f"Meilleur fournisseur : {eval_result.best_offer}",
        "",
        "Classement des offres :",
    ]
    for s in eval_result.scores:
        score_val = getattr(s, "overall_score", None) or getattr(s, "performance_score", None)
        score_str = f"{score_val:.1f}/10" if score_val is not None else "N/A"
        lines.append(f"  #{s.rank}. {s.supplier_name} — Score: {score_str}")

    lines += [
        "",
        "Cordialement,",
        "Procurement AI System",
    ]
    body = "\n".join(lines)

    sender = EmailSender()
    attachment = eval_result.report_path if eval_result.report_path else None
    sender.send(
        to_email=requester_email,
        subject=f"Résultats d'appel d'offres — {product}",
        body=body,
        attachment_path=attachment,
    )
    logger.info("Evaluation report sent", extra={"to": requester_email, "product": product})


def _send_no_offer_notification(requester_email: str, product: str) -> None:
    """Notify requester that no offers were received before the deadline."""
    if not requester_email:
        return
    try:
        sender = EmailSender()
        sender.send(
            to_email=requester_email,
            subject=f"Appel d'offres — Aucune réponse reçue — {product}",
            body=(
                f"Bonjour,\n\n"
                f"Le délai de réponse pour votre demande de : {product} est écoulé.\n"
                f"Malheureusement, aucun fournisseur n'a répondu à l'appel d'offres.\n\n"
                f"Vous pouvez soumettre une nouvelle demande si vous le souhaitez.\n\n"
                f"Cordialement,\nProcurement AI System"
            ),
        )
    except Exception as exc:
        logger.warning("Failed to send no-offer notification", extra={"error": str(exc)})
