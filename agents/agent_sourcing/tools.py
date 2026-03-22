"""
agents/agent_sourcing/tools.py
Tools used by the Sourcing Agent — internal DB search + Tavily web search + email scraping.
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional

import requests
from strands import tool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from logger import get_logger

logger = get_logger(__name__)

# ── Email extraction helpers ─────────────────────────────────────────────────

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SKIP_PREFIXES = ("noreply", "no-reply", "example", "test", "donotreply", "webmaster", "info@example")

# Common contact page paths to try when scraping a supplier's website
_CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactez-nous",
    "/nous-contacter", "/contact.html", "/about", "/a-propos",
]


def _scrape_email_from_url(url: str) -> Optional[str]:
    """
    Fetch a URL and extract the first valid email from its HTML.
    Returns None if no email found or request fails.
    """
    try:
        resp = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ProcurementBot/1.0)"},
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return None
        from bs4 import BeautifulSoup
        text = BeautifulSoup(resp.text, "html.parser").get_text(separator=" ")
        for email in EMAIL_PATTERN.findall(text):
            if not any(email.lower().startswith(p) for p in SKIP_PREFIXES):
                return email
    except Exception:
        pass
    return None


# ── Strands @tool functions ──────────────────────────────────────────────────

@tool
def log_sourcing_decision(
    supplier_name: str,
    action: str,
    reason: str,
    supplier_email: str = "",
    supplier_website: str = "",
    source: str = "web_search",
    relevance_score: float = 0.0,
    search_query: str = "",
) -> str:
    """
    Log a sourcing decision for audit trail. Call this for EACH supplier you evaluate.

    Args:
        supplier_name: Name of the supplier
        action: One of: 'retained', 'excluded', 'no_email', 'duplicate'
        reason: Why this supplier was retained or excluded (e.g. "relevant to category, has email",
                "no contact email found", "duplicate of existing supplier", "marketplace excluded")
        supplier_email: Supplier email if available
        supplier_website: Supplier website URL
        source: 'internal_db' or 'web_search'
        relevance_score: Score assigned (0.0 to 1.0)
        search_query: The search query that found this supplier

    Returns:
        JSON confirmation.
    """
    try:
        from db.models import SourcingAuditLog, get_engine, get_session_factory, create_tables

        engine = get_engine()
        create_tables(engine)
        Session = get_session_factory(engine)
        session = Session()
        try:
            entry = SourcingAuditLog(
                supplier_name=supplier_name,
                supplier_email=supplier_email or None,
                supplier_website=supplier_website or None,
                source=source,
                action=action,
                reason=reason,
                relevance_score=relevance_score,
                search_query=search_query,
            )
            session.add(entry)
            session.commit()
            logger.info("Sourcing audit logged", extra={
                "supplier": supplier_name, "action": action, "reason": reason,
            })
            return json.dumps({"status": "logged", "supplier": supplier_name, "action": action})
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Audit log failed", extra={"error": str(exc)})
        return json.dumps({"status": "log_failed", "error": str(exc)})


@tool
def search_existing_suppliers(product: str, category: str) -> str:
    """
    Search the internal database for existing suppliers matching the product/category.
    Call this FIRST before searching the web — reusing known suppliers is faster and more reliable.

    Args:
        product: Product or service name (e.g. "wooden office desk")
        category: Procurement category (e.g. "Office Supplies")

    Returns:
        JSON array of existing suppliers from the database with keys:
        name, website, email, country, category, relevance_score, source_url.
        Returns an empty array if no matches found.
    """
    try:
        from db.models import Supplier, get_engine, get_session_factory
        from sqlalchemy import or_, func

        engine = get_engine()
        Session = get_session_factory(engine)
        session = Session()

        try:
            # Search by category match or product keyword in name/category
            product_lower = product.lower()
            category_lower = category.lower()

            query = session.query(Supplier).filter(
                Supplier.email.isnot(None),
                Supplier.email != "",
            )

            # Try category match first, then broader keyword search
            results = query.filter(
                func.lower(Supplier.category).contains(category_lower)
            ).all()

            if not results:
                # Broader search: match any keyword from product in supplier category/name
                keywords = [w for w in product_lower.split() if len(w) > 3]
                if keywords:
                    conditions = []
                    for kw in keywords:
                        conditions.append(func.lower(Supplier.category).contains(kw))
                        conditions.append(func.lower(Supplier.name).contains(kw))
                    results = query.filter(or_(*conditions)).all()

            # Deduplicate by email
            seen_emails = set()
            unique = []
            for s in results:
                if s.email and s.email.lower() not in seen_emails:
                    seen_emails.add(s.email.lower())
                    unique.append(s)

            suppliers = [
                {
                    "name": s.name,
                    "website": s.website or "",
                    "email": s.email,
                    "country": s.country or "Tunisia",
                    "category": s.category or category,
                    "relevance_score": float(s.relevance_score or 0.7),
                    "source_url": s.source_url or "",
                    "source": "internal_db",
                }
                for s in unique[:12]
            ]

            logger.info("Internal DB supplier search", extra={
                "product": product, "category": category, "found": len(suppliers),
            })
            return json.dumps(suppliers, ensure_ascii=False)

        finally:
            session.close()

    except Exception as exc:
        logger.warning("Internal DB search failed", extra={"error": str(exc)})
        return json.dumps([])


@tool
def search_suppliers(product: str, category: str, max_results: int = 12) -> str:
    """
    Search for Tunisian suppliers using Tavily Search API.

    Args:
        product: Product or service name (e.g. "wooden office desk")
        category: Procurement category (e.g. "Office Supplies")
        max_results: Maximum number of results to return (default 12)

    Returns:
        JSON array of raw search results with keys: title, url, content, score.
        Returns an empty array if Tavily key is not configured or search fails.
    """
    if not settings.tavily_api_key:
        logger.warning("Tavily API key not configured — skipping supplier search")
        return json.dumps([])

    # Build multiple targeted queries for better coverage
    queries = [
        f"acheter {product} Tunisie site:.tn",
        f"{product} distributeur revendeur Tunisie",
        f"{product} {category} fournisseur Tunisie",
    ]

    all_results = []
    seen_urls = set()

    exclude = [
        "amazon.com", "ebay.com", "alibaba.com", "aliexpress.com",
        "facebook.com", "youtube.com", "wikipedia.org", "linkedin.com",
    ]

    for query in queries:
        logger.info("Searching Tunisian suppliers via Tavily", extra={"query": query})
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_domains": [],
                    "exclude_domains": exclude,
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

            for r in data.get("results", []):
                url = r.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({
                        "title": r.get("title", ""),
                        "url": url,
                        "content": r.get("content", "")[:400],
                        "score": round(r.get("score", 0.0), 3),
                    })
        except requests.RequestException as exc:
            logger.warning("Tavily search failed for query", extra={"query": query, "error": str(exc)})
            continue

    # Prioritize .tn domains
    all_results.sort(key=lambda r: (0 if ".tn" in r["url"] else 1, -r["score"]))
    simplified = all_results[:max_results]

    return json.dumps(simplified, ensure_ascii=False)


@tool
def get_supplier_contact(supplier_name: str, website: str) -> str:
    """
    Find a supplier's contact email using two strategies:
    1. Direct scraping of the supplier's contact page (most reliable).
    2. Tavily search fallback if scraping finds nothing.

    Args:
        supplier_name: Name of the company (e.g. "Korsi.tn")
        website: Company website URL (e.g. "https://korsi.tn")

    Returns:
        JSON object with key "email" (string or null).
    """
    logger.info("Looking up supplier contact", extra={"supplier": supplier_name, "website": website})

    base = website.rstrip("/")

    # ── Strategy 1: direct page scraping ──────────────────────────────────────
    for path in _CONTACT_PATHS:
        email = _scrape_email_from_url(f"{base}{path}")
        if email:
            logger.info("Email found via scraping", extra={"supplier": supplier_name, "email": email})
            return json.dumps({"email": email})

    # Also try the homepage itself
    email = _scrape_email_from_url(base)
    if email:
        logger.info("Email found on homepage", extra={"supplier": supplier_name, "email": email})
        return json.dumps({"email": email})

    # ── Strategy 2: Tavily fallback ────────────────────────────────────────────
    if settings.tavily_api_key:
        try:
            domain = base.replace("https://", "").replace("http://", "").split("/")[0]
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": f"{supplier_name} email contact",
                    "search_depth": "basic",
                    "max_results": 3,
                    "include_domains": [domain] if domain else [],
                },
                timeout=10,
            )
            response.raise_for_status()
            for result in response.json().get("results", []):
                for email in EMAIL_PATTERN.findall(result.get("content", "")):
                    if not any(email.lower().startswith(p) for p in SKIP_PREFIXES):
                        logger.info("Email found via Tavily", extra={"supplier": supplier_name, "email": email})
                        return json.dumps({"email": email})
        except requests.RequestException as exc:
            logger.warning("Tavily contact fallback failed", extra={"error": str(exc)})

    logger.info("No email found", extra={"supplier": supplier_name})
    return json.dumps({"email": None})
