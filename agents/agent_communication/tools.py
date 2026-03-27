"""
agents/agent_communication/tools.py
Tools used by the Communication Agent — email sending, inbox monitoring,
supplier email recovery, and reminder logic.
"""
import io
import json
import imaplib
import email as email_lib
from datetime import datetime, timezone
from strands import tool

import pdfplumber

from config import settings
from email_gateway.sender import EmailSender
from logger import get_logger

logger = get_logger(__name__)

# ── Dry-run mode (set via run_pipeline.py --dry-run) ─────────────────────────
DRY_RUN = False

# Reuse scraping logic from sourcing agent
from agents.agent_sourcing.tools import _scrape_email_from_url, _CONTACT_PATHS


# ── RFQ email sending ────────────────────────────────────────────────────────

@tool
def send_email_to_supplier(
    to_email: str,
    supplier_name: str,
    subject: str,
    body: str,
) -> str:
    """
    Send an RFQ or reminder email to a supplier.

    Args:
        to_email: Supplier's email address
        supplier_name: Company name (for logging)
        subject: Email subject line
        body: Full email body text

    Returns:
        JSON with keys: status ("sent" | "failed"), message_id, error.
    """
    logger.info("Sending email to supplier", extra={"supplier": supplier_name, "to": to_email})

    if DRY_RUN:
        logger.info("[DRY-RUN] Skipping real email send", extra={"supplier": supplier_name, "to": to_email})
        print(f"  [DRY-RUN] Would send RFQ to {supplier_name} <{to_email}>")
        print(f"            Subject: {subject}")
        return json.dumps({
            "status": "sent",
            "message_id": f"dry-run-{supplier_name}",
            "error": None,
        })

    try:
        sender = EmailSender()
        message_id = sender.send(to_email=to_email, subject=subject, body=body)
        logger.info("Email sent", extra={"supplier": supplier_name, "message_id": message_id})
        return json.dumps({
            "status": "sent",
            "message_id": message_id,
            "error": None,
        })
    except Exception as exc:
        logger.error("Email send failed", extra={"supplier": supplier_name, "error": str(exc)})
        return json.dumps({
            "status": "failed",
            "message_id": None,
            "error": str(exc),
        })


# ── Supplier email recovery ──────────────────────────────────────────────────

@tool
def retry_find_supplier_email(supplier_name: str, website: str) -> str:
    """
    Last-attempt to find a supplier's email by scraping their website.
    Called for suppliers where Agent 2 returned email=null.

    Args:
        supplier_name: Company name
        website: Company website URL

    Returns:
        JSON with key "email" (string or null).
    """
    logger.info("Retrying email lookup", extra={"supplier": supplier_name, "website": website})

    base = website.rstrip("/")

    # Try contact pages
    for path in _CONTACT_PATHS:
        found = _scrape_email_from_url(f"{base}{path}")
        if found:
            logger.info("Email recovered via scraping", extra={"supplier": supplier_name, "email": found})
            return json.dumps({"email": found})

    # Try homepage
    found = _scrape_email_from_url(base)
    if found:
        logger.info("Email recovered from homepage", extra={"supplier": supplier_name, "email": found})
        return json.dumps({"email": found})

    logger.info("Email recovery failed", extra={"supplier": supplier_name})
    return json.dumps({"email": None})


# ── Inbox monitoring ─────────────────────────────────────────────────────────

@tool
def fetch_supplier_replies(rfq_subject_prefix: str, received_after: str = "") -> str:
    """
    Check Gmail inbox for supplier replies to RFQ emails.
    Looks for emails whose subject contains the RFQ subject prefix.

    Args:
        rfq_subject_prefix: The subject prefix used in sent RFQs
                            (e.g. "RFQ — ergonomic office chairs")
        received_after: ISO datetime string — only return emails received after
                        this timestamp (e.g. "2026-03-27T14:00:00+00:00").
                        Defaults to today's date to avoid picking up old emails.

    Returns:
        JSON array of reply objects with keys:
        from_email, subject, body, received_at.
        Returns empty array if no replies found or IMAP fails.
    """
    if DRY_RUN:
        logger.info("[DRY-RUN] Returning simulated supplier replies")
        print(f"  [DRY-RUN] Simulating 5 supplier replies for: {rfq_subject_prefix}")
        fake_replies = [
            {
                "from_email": "ventes@cosmetiques-tunisia.tn",
                "subject": f"Re: {rfq_subject_prefix}",
                "body": (
                    "Bonjour,\n\n"
                    "Suite à votre demande de devis, veuillez trouver notre offre :\n"
                    "- Produit : L'Oréal Elseve Total Repair 5 Shampooing 250ml\n"
                    "- Prix unitaire : 12.500 TND HT\n"
                    "- Délai de livraison : 3 jours ouvrables\n"
                    "- Garantie : Produit original, date d'expiration > 18 mois\n"
                    "- Conditions de paiement : Net 30 jours\n"
                    "- Livraison gratuite à partir de 100 unités\n"
                    "- Distributeur agréé L'Oréal, certification ISO 9001\n\n"
                    "Cordialement,\nKarim Ben Salah\nCosmétiques Tunisia SARL"
                ),
                "has_pdf": False,
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "from_email": "commercial@beaute-pro.tn",
                "subject": f"Re: {rfq_subject_prefix}",
                "body": (
                    "Madame, Monsieur,\n\n"
                    "Nous avons le plaisir de vous soumettre notre proposition :\n"
                    "- Produit : L'Oréal Elseve Color-Vive Shampooing 250ml\n"
                    "- Prix unitaire : 14.800 TND HT\n"
                    "- Délai de livraison : 5 jours ouvrables\n"
                    "- Garantie : Produit authentique, traçabilité complète\n"
                    "- Conditions de paiement : 50% à la commande, solde à la livraison\n"
                    "- Stock permanent : 2000+ unités\n"
                    "- Certification RSE et emballage éco-responsable\n\n"
                    "Restant à votre disposition,\nSonia Maalej\nBeauté Pro Distribution"
                ),
                "has_pdf": False,
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "from_email": "info@hygiene-express.tn",
                "subject": f"Re: {rfq_subject_prefix}",
                "body": (
                    "Bonjour,\n\n"
                    "En réponse à votre appel d'offres, voici notre meilleure proposition :\n"
                    "- Produit : L'Oréal Elseve Arginine Resist x3 Shampooing 400ml\n"
                    "- Prix unitaire : 18.900 TND HT\n"
                    "- Délai de livraison : 7 jours ouvrables\n"
                    "- Garantie : 2 ans avant expiration\n"
                    "- Conditions de paiement : Net 45 jours\n"
                    "- Format économique 400ml, meilleur rapport qualité/prix\n"
                    "- Fournisseur certifié ISO 14001, engagement RSE\n\n"
                    "Bien cordialement,\nAhmed Trabelsi\nHygiène Express"
                ),
                "has_pdf": False,
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "from_email": "devis@parapharma-direct.tn",
                "subject": f"Re: {rfq_subject_prefix}",
                "body": (
                    "Bonjour,\n\n"
                    "Merci pour votre consultation. Voici notre offre :\n"
                    "- Produit : L'Oréal Elseve Huile Extraordinaire Shampooing 250ml\n"
                    "- Prix unitaire : 16.200 TND HT\n"
                    "- Délai de livraison : 10 jours ouvrables\n"
                    "- Garantie : Produit original sous scellé\n"
                    "- Conditions de paiement : Net 30 jours\n"
                    "- Gamme premium, forte demande client\n"
                    "- Pas de certification RSE\n\n"
                    "Cordialement,\nMehdi Gharbi\nParaPharma Direct"
                ),
                "has_pdf": False,
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "from_email": "contact@soins-sahara.tn",
                "subject": f"Re: {rfq_subject_prefix}",
                "body": (
                    "Bonjour,\n\n"
                    "Nous vous remercions pour votre consultation. Notre offre :\n"
                    "- Produit : L'Oréal Elseve Dream Long Shampooing 250ml\n"
                    "- Prix unitaire : 13.500 TND HT\n"
                    "- Délai de livraison : 14 jours\n"
                    "- Garantie : Produit certifié, lot traçable\n"
                    "- Conditions de paiement : Net 60 jours\n"
                    "- Grossiste agréé, prix dégressif dès 200 unités\n"
                    "- Fournisseur certifié ISO 14001 (RSE)\n\n"
                    "Cordialement,\nFatma Bouazizi\nSoins Sahara Distribution"
                ),
                "has_pdf": False,
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
        return json.dumps(fake_replies, ensure_ascii=False)

    if not settings.gmail_address or not settings.gmail_app_password:
        logger.warning("Gmail credentials not configured — cannot check inbox")
        return json.dumps([])

    logger.info("Checking inbox for RFQ replies", extra={"prefix": rfq_subject_prefix})

    password = settings.gmail_app_password.replace(" ", "")

    try:
        conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        conn.login(settings.gmail_address, password)
        conn.select("INBOX")

        # Search for emails with matching subject
        # Use just "RFQ" keyword — the full prefix with special chars (em dash)
        # can cause IMAP encoding issues. We filter more precisely below.
        simple_keyword = "RFQ"
        if rfq_subject_prefix:
            # Extract the first plain-ASCII word chunk for a reliable IMAP match
            for word in rfq_subject_prefix.split():
                if word.isascii() and len(word) > 2 and word.isalpha():
                    simple_keyword = word
                    break
        # Build IMAP SINCE filter — use received_after date or today as minimum
        since_dt = None
        if received_after:
            try:
                since_dt = datetime.fromisoformat(received_after.replace("Z", "+00:00"))
            except Exception:
                pass
        if since_dt is None:
            since_dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        imap_since = since_dt.strftime("%d-%b-%Y")
        search_query = f'(SUBJECT "{simple_keyword}" SINCE "{imap_since}")'

        _, msg_nums = conn.search(None, search_query)
        ids = msg_nums[0].split()

        replies = []
        for num in ids:
            _, data = conn.fetch(num, "(RFC822)")
            raw = data[0][1]
            msg = email_lib.message_from_bytes(raw)

            from_addr = msg.get("From", "")
            # Skip our own sent messages
            if settings.gmail_address.lower() in from_addr.lower():
                continue

            # Extract body text and PDF attachments
            body_text = ""
            pdf_texts = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    disposition = str(part.get("Content-Disposition", ""))

                    # Plain text body
                    if content_type == "text/plain" and "attachment" not in disposition:
                        payload = part.get_payload(decode=True)
                        if payload and not body_text:
                            body_text = payload.decode("utf-8", errors="replace")

                    # PDF attachment
                    elif content_type == "application/pdf":
                        payload = part.get_payload(decode=True)
                        if payload:
                            pdf_text = _extract_text_from_pdf(payload)
                            if pdf_text:
                                filename = part.get_filename() or "attachment.pdf"
                                pdf_texts.append(f"[PDF: {filename}]\n{pdf_text}")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body_text = payload.decode("utf-8", errors="replace")

            # Combine body + PDF content
            full_body = body_text.strip()
            if pdf_texts:
                full_body += "\n\n--- PDF ATTACHMENTS ---\n" + "\n\n".join(pdf_texts)

            # Extract sender email from "Name <email>" format
            sender_email = from_addr
            if "<" in from_addr and ">" in from_addr:
                sender_email = from_addr.split("<")[1].split(">")[0]

            received_at_raw = msg.get("Date", "")

            # Post-fetch time filter: skip emails before received_after
            if since_dt and received_at_raw:
                try:
                    import email.utils as _eutils
                    msg_dt = _eutils.parsedate_to_datetime(received_at_raw)
                    if msg_dt.tzinfo is None:
                        msg_dt = msg_dt.replace(tzinfo=timezone.utc)
                    if msg_dt < since_dt:
                        continue
                except Exception:
                    pass

            replies.append({
                "from_email": sender_email.strip(),
                "subject": msg.get("Subject", ""),
                "body": full_body[:5000],
                "has_pdf": len(pdf_texts) > 0,
                "received_at": received_at_raw,
            })

        conn.logout()

        logger.info("Found replies", extra={"count": len(replies), "prefix": rfq_subject_prefix})
        return json.dumps(replies, ensure_ascii=False)

    except Exception as exc:
        logger.error("IMAP fetch failed", extra={"error": str(exc)})
        return json.dumps([])


# ── Helpers (non-tool) ────────────────────────────────────────────────────────

def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF file (in-memory bytes).
    Falls back to OCR (pytesseract) if pdfplumber extracts no text (scanned PDF).
    """
    # Step 1: Try text extraction with pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages[:20]:
                text = page.extract_text()
                if text:
                    pages.append(text)
            if pages:
                return "\n".join(pages)[:4000]
    except Exception as exc:
        logger.warning("pdfplumber extraction failed", extra={"error": str(exc)})

    # Step 2: Fallback to OCR for scanned PDFs
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        logger.info("Falling back to OCR for scanned PDF")
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=10)
        ocr_pages = []
        for img in images:
            text = pytesseract.image_to_string(img, lang="eng+fra")
            if text and text.strip():
                ocr_pages.append(text.strip())
        if ocr_pages:
            return "\n".join(ocr_pages)[:4000]
    except ImportError:
        logger.warning("OCR dependencies not available (pdf2image/pytesseract)")
    except Exception as exc:
        logger.warning("OCR extraction failed", extra={"error": str(exc)})

    return ""


def is_reminder_due(sent_at: str, hours_threshold: int = 72) -> bool:
    """Check if enough time has passed since the RFQ was sent to warrant a reminder."""
    try:
        sent_time = datetime.fromisoformat(sent_at)
        if sent_time.tzinfo is None:
            sent_time = sent_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        elapsed_hours = (now - sent_time).total_seconds() / 3600
        return elapsed_hours >= hours_threshold
    except (ValueError, TypeError):
        return False
