"""
agents/analysis/agent.py
Analysis Agent — extracts a structured ProcurementSpec from
a requester's free-text email using Claude Sonnet 4 via Strands.
"""
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from strands import Agent
from strands.models import BedrockModel

# Ensure project root is importable when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """
You are a procurement analysis specialist. Your job is to extract structured
procurement information from a requester's email written in French or English.

You MUST return a valid JSON object with these exact fields:
{
  "product": "string — product or service name",
  "category": "string — broad category (e.g. 'Fournitures de bureau', 'Matériel informatique')",
  "quantity": number or null,
  "unit": "string — e.g. 'unités', 'kg', 'boîtes' or null",
  "budget_min": number or null,
  "budget_max": number or null,
  "deadline": "ISO date string YYYY-MM-DD or null",
  "requester_email": "string — email of the sender",
  "is_valid": true or false,
  "rejection_reason": "string if is_valid is false, else null"
}

Rules:
- is_valid = false if product is missing or the email is unclear
- All monetary values in TND (Tunisian Dinar)
- If budget not mentioned, set both to null
- Return ONLY the JSON object, no extra text
"""


@dataclass
class ProcurementSpec:
    product: str
    category: str
    quantity: Optional[float]
    unit: Optional[str]
    budget_min: Optional[float]
    budget_max: Optional[float]
    deadline: Optional[str]
    requester_email: str
    is_valid: bool
    rejection_reason: Optional[str] = None


class AnalysisAgent:
    """Extracts a ProcurementSpec from a raw requester email."""

    def __init__(self):
        model = BedrockModel(
            model_id=settings.bedrock_model_id,
            region_name=settings.aws_region,
        )
        self._agent = Agent(model=model, system_prompt=SYSTEM_PROMPT)

    def analyze(self, email_body: str, requester_email: str) -> ProcurementSpec:
        logger.info("Analysis Agent invoked", extra={"requester": requester_email})

        prompt = f"""
Requester email: {requester_email}

Email body:
---
{email_body}
---

Extract the procurement information and return JSON.
"""
        try:
            response = self._agent(prompt)
            # Extract text from Strands response
            raw = str(response).strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw.strip())
        except json.JSONDecodeError as exc:
            logger.error("JSON parse failed", extra={"error": str(exc)})
            return ProcurementSpec(
                product="", category="", quantity=None, unit=None,
                budget_min=None, budget_max=None, deadline=None,
                requester_email=requester_email,
                is_valid=False,
                rejection_reason="LLM returned invalid JSON",
            )

        return ProcurementSpec(
            product=data.get("product", ""),
            category=data.get("category", ""),
            quantity=data.get("quantity"),
            unit=data.get("unit"),
            budget_min=data.get("budget_min"),
            budget_max=data.get("budget_max"),
            deadline=data.get("deadline"),
            requester_email=data.get("requester_email", requester_email),
            is_valid=data.get("is_valid", False),
            rejection_reason=data.get("rejection_reason"),
        )


# ═══════════════════════════════════════════════════════════════════
# LIVE MODE  —  python agents/analysis/agent.py
# Watches Gmail inbox every 15 s. Ctrl+C to stop.
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import imaplib
    import sys
    import os
    import time
    from dataclasses import asdict
    from datetime import datetime
    from dotenv import load_dotenv

    # ── Fix 1: force-load .env from the project root ──────────────
    # Works whether you run from: project/, agents/, or agents/analysis/
    _here = os.path.abspath(__file__)
    _root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
    _env_path = os.path.join(_root, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=True)
        # Reload settings after dotenv is loaded
        from importlib import reload
        import config as _cfg
        reload(_cfg)
        from config import settings
    else:
        print(f"⚠️  .env not found at {_env_path}")
        print("    Create it from .env.example and fill in your credentials.")
        sys.exit(1)

    # Make sure project root is on PYTHONPATH
    sys.path.insert(0, _root)
    from email_gateway.parser import EmailParser

    POLL_INTERVAL = 15
    OUTPUT_DIR = os.path.join(_root, "outputs")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    agent = AnalysisAgent()
    parser = EmailParser()

    # ── Fix 2: strip spaces from App Password ─────────────────────
    # Google shows: "xxxx xxxx xxxx xxxx" — IMAP needs: "xxxxxxxxxxxxxxxx"
    _password = settings.gmail_app_password.replace(" ", "")


    def process_email(raw_bytes: bytes):
        parsed = parser.parse(raw_bytes)

        print(f"\n{'='*60}")
        print(f"📨  Nouvel email — {datetime.now().strftime('%H:%M:%S')}")
        print(f"    De      : {parsed.from_email}")
        print(f"    Objet   : {parsed.subject}")
        print(f"    Corps   : {parsed.body[:200].strip()!r}")
        print(f"{'='*60}")

        print("🤖  Analyse en cours (Claude Sonnet 4)...")
        spec = agent.analyze(parsed.body, parsed.from_email)

        if spec.is_valid:
            print(f"\n✅  Demande valide !")
            print(f"    Produit   : {spec.product}")
            print(f"    Catégorie : {spec.category}")
            print(f"    Quantité  : {spec.quantity} {spec.unit or ''}")
            print(f"    Budget    : {spec.budget_min or 'N/A'} – {spec.budget_max or 'N/A'} TND")
            print(f"    Deadline  : {spec.deadline or 'Non précisée'}")
        else:
            print(f"\n❌  Demande rejetée : {spec.rejection_reason}")

        # Save result to JSON
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = "valid" if spec.is_valid else "rejected"
        filename = f"analysis_{label}_{ts}.json"
        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            import json as _json
            _json.dump(asdict(spec), f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾  Résultat → {out_path}")

    def poll_once(conn: imaplib.IMAP4_SSL) -> int:
        """Check for UNSEEN emails. Returns number processed."""
        conn.select("INBOX")
        _, msg_nums = conn.search(None, "UNSEEN")
        ids = msg_nums[0].split()
        for num in ids:
            _, data = conn.fetch(num, "(RFC822)")
            raw = data[0][1]
            conn.store(num, "+FLAGS", "\\Seen")   # mark as read
            try:
                process_email(raw)
            except Exception as exc:
                print(f"⚠️   Erreur lors du traitement : {exc}")
        return len(ids)

    # ── Main loop ─────────────────────────────────────────────────
    print(f"\n🚀  Analysis Agent — mode surveillance active")
    print(f"    Boîte    : {settings.gmail_address}")
    print(f"    Intervalle: toutes les {POLL_INTERVAL} secondes")
    print(f"    Arrêt    : Ctrl+C\n")

    conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    conn.login(settings.gmail_address, _password)
    print(f"✅  Connecté à Gmail — surveillance en cours...\n")

    try:
        while True:
            try:
                n = poll_once(conn)
                if n == 0:
                    print(f"📭  [{datetime.now().strftime('%H:%M:%S')}] Aucun nouveau mail — prochain check dans {POLL_INTERVAL}s")
            except imaplib.IMAP4.abort:
                # Connection dropped — reconnect silently
                conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
                conn.login(settings.gmail_address, settings.gmail_app_password)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n🛑  Surveillance arrêtée.")
        conn.logout()

