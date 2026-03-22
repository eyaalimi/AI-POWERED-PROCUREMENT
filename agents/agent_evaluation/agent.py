"""
agents/agent_evaluation/agent.py
Evaluation Agent — scores supplier offers using the QCDP matrix and ranks them.

No LLM needed — pure algorithmic scoring.

QCDP Matrix:
  - Qualité (Q)      : 25%  — warranty duration + quality signals
  - Coût (C)         : 35%  — price competitiveness + budget fit
  - Délais (D)       : 20%  — delivery speed
  - Performance (P)  : 20%  — payment terms + RSE/local bonus

Input  : list of SupplierOffer dicts + ProcurementSpec dict
Output : EvaluationResult with ranked OfferScores + PDF report path
"""
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from logger import get_logger

logger = get_logger(__name__)

# ── QCDP Weights ─────────────────────────────────────────────────────────────

QCDP_WEIGHTS = {
    "qualite": 0.25,      # Q — warranty + quality signals
    "cout": 0.35,         # C — price competitiveness + budget fit
    "delais": 0.20,       # D — delivery speed
    "performance": 0.20,  # P — payment terms + RSE/local bonus
}


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class OfferScore:
    """Detailed score breakdown for one supplier offer (QCDP matrix)."""
    supplier_name: str
    supplier_email: str
    unit_price: Optional[float]
    total_price: Optional[float]
    currency: str
    delivery_days: Optional[int]
    warranty: Optional[str]
    payment_terms: Optional[str]
    # QCDP sub-scores (0–100)
    price_score: float
    delivery_score: float
    warranty_score: float
    payment_score: float
    budget_fit_score: float
    rse_score: float
    # QCDP axis scores (0–100)
    qualite_score: float
    cout_score: float
    delais_score: float
    performance_score: float
    overall_score: float
    rank: int
    recommendation: str


@dataclass
class EvaluationResult:
    """Full output of the Evaluation Agent."""
    request_product: str
    scores: list        # list[OfferScore]
    best_offer: Optional[str]  # supplier name
    report_path: Optional[str]  # path to generated PDF
    timestamp: str


# ── Scoring helpers ──────────────────────────────────────────────────────────

def _score_price(prices: list[Optional[float]], idx: int) -> float:
    """Score based on relative price (lowest gets 100)."""
    valid = [p for p in prices if p is not None and p > 0]
    if not valid or prices[idx] is None or prices[idx] <= 0:
        return 0.0
    min_price = min(valid)
    return round((min_price / prices[idx]) * 100, 1)


def _score_delivery(days_list: list[Optional[int]], idx: int) -> float:
    """Score based on delivery time (fastest gets 100)."""
    valid = [d for d in days_list if d is not None and d > 0]
    if not valid or days_list[idx] is None or days_list[idx] <= 0:
        return 0.0
    min_days = min(valid)
    return round((min_days / days_list[idx]) * 100, 1)


def _parse_warranty_months(warranty: Optional[str]) -> int:
    """Extract warranty duration in months from text."""
    if not warranty:
        return 0
    text = warranty.lower()
    # Try "X year(s)"
    match = re.search(r"(\d+)\s*year", text)
    if match:
        return int(match.group(1)) * 12
    # Try "X month(s)"
    match = re.search(r"(\d+)\s*month", text)
    if match:
        return int(match.group(1))
    # Try "X mois" (French)
    match = re.search(r"(\d+)\s*mois", text)
    if match:
        return int(match.group(1))
    # Try "X an(s)" (French)
    match = re.search(r"(\d+)\s*an", text)
    if match:
        return int(match.group(1)) * 12
    return 0


def _score_warranty(warranties: list[Optional[str]], idx: int) -> float:
    """Score based on warranty duration (longest gets 100)."""
    months = [_parse_warranty_months(w) for w in warranties]
    max_months = max(months) if months else 0
    if max_months == 0 or months[idx] == 0:
        return 0.0
    return round((months[idx] / max_months) * 100, 1)


def _parse_payment_days(terms: Optional[str]) -> int:
    """Extract net payment days from text (e.g. '30 days net' -> 30)."""
    if not terms:
        return 0
    text = terms.lower()
    match = re.search(r"(\d+)\s*(?:days?|jours?)", text)
    if match:
        return int(match.group(1))
    return 0


def _score_payment(terms_list: list[Optional[str]], idx: int) -> float:
    """Score based on payment terms (longer net days is better for buyer)."""
    days = [_parse_payment_days(t) for t in terms_list]
    max_days = max(days) if days else 0
    if max_days == 0 or days[idx] == 0:
        return 0.0
    return round((days[idx] / max_days) * 100, 1)


def _score_rse(offer: dict) -> float:
    """Score RSE / local performance signals (0–100).

    Heuristics:
      - Tunisian supplier (.tn email/website or country=Tunisia) → +40
      - Certifications mentioned (ISO, CE, NF, etc.) → +30
      - Warranty present → +15
      - Notes mentioning eco/RSE keywords → +15
    """
    score = 0.0
    country = (offer.get("country") or "").lower()
    email = (offer.get("supplier_email") or "").lower()
    website = (offer.get("website") or offer.get("source_url") or "").lower()
    notes = (offer.get("notes") or "").lower()
    warranty = offer.get("warranty") or ""

    # Local / Tunisian bonus
    if "tunis" in country or email.endswith(".tn") or ".tn" in website:
        score += 40

    # Certifications
    cert_keywords = ["iso", "ce ", "nf ", "certification", "certifié", "certified", "haccp"]
    if any(k in notes for k in cert_keywords):
        score += 30

    # Warranty presence
    if warranty.strip():
        score += 15

    # Eco / RSE keywords
    rse_keywords = ["rse", "éco", "eco", "durable", "sustainable", "environnement", "green"]
    if any(k in notes for k in rse_keywords):
        score += 15

    return min(score, 100.0)


def _score_budget_fit(total_price: Optional[float], budget_max: Optional[float]) -> float:
    """Score based on how well the price fits within budget."""
    if total_price is None or budget_max is None or budget_max <= 0:
        return 50.0  # Neutral if unknown
    if total_price <= budget_max:
        # Under budget — score proportional to savings
        savings_ratio = (budget_max - total_price) / budget_max
        return round(70 + savings_ratio * 30, 1)  # 70–100
    else:
        # Over budget — penalize
        over_ratio = (total_price - budget_max) / budget_max
        return round(max(0, 70 - over_ratio * 100), 1)


def _generate_recommendation(score: "OfferScore", rank: int, total: int) -> str:
    """Generate a text recommendation based on QCDP axes."""
    if rank == 1:
        parts = ["Meilleure offre globale"]
        if score.cout_score >= 90:
            parts.append("meilleur coût")
        if score.delais_score >= 90:
            parts.append("délais les plus courts")
        if score.qualite_score >= 90:
            parts.append("qualité supérieure")
        return " — ".join(parts)
    elif rank == total:
        return "Offre la moins compétitive"
    else:
        strengths = []
        if score.cout_score >= 80:
            strengths.append("coût compétitif")
        if score.delais_score >= 80:
            strengths.append("bons délais")
        if score.qualite_score >= 80:
            strengths.append("bonne qualité")
        if score.performance_score >= 80:
            strengths.append("bonne performance/RSE")
        if strengths:
            return "Bonne option — " + ", ".join(strengths)
        return "Offre moyenne"


# ── Agent class ──────────────────────────────────────────────────────────────

class EvaluationAgent:
    """Scores and ranks supplier offers, generates PDF comparison report."""

    def evaluate(
        self,
        offers: list,
        procurement_spec: dict,
        generate_pdf: bool = True,
        output_dir: str = None,
    ) -> EvaluationResult:
        """
        Evaluate and rank supplier offers.

        Args:
            offers: list of SupplierOffer dicts
            procurement_spec: ProcurementSpec dict (for budget context)
            generate_pdf: whether to generate a PDF report
            output_dir: directory for PDF output (default: outputs/)

        Returns:
            EvaluationResult with ranked scores and optional PDF path.
        """
        product = procurement_spec.get("product", "Unknown")
        budget_max = procurement_spec.get("budget_max")

        if not offers:
            logger.info("No offers to evaluate")
            return EvaluationResult(
                request_product=product,
                scores=[],
                best_offer=None,
                report_path=None,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Convert dataclasses to dicts if needed
        offer_dicts = []
        for o in offers:
            if hasattr(o, "__dict__") and not isinstance(o, dict):
                offer_dicts.append(asdict(o))
            else:
                offer_dicts.append(o)

        logger.info("Evaluating offers", extra={
            "product": product, "offer_count": len(offer_dicts),
        })

        # Extract lists for comparative scoring
        prices = [o.get("total_price") for o in offer_dicts]
        delivery_days = [o.get("delivery_days") for o in offer_dicts]
        warranties = [o.get("warranty") for o in offer_dicts]
        payment_terms = [o.get("payment_terms") for o in offer_dicts]

        # Score each offer using QCDP matrix
        scored = []
        for i, o in enumerate(offer_dicts):
            ps = _score_price(prices, i)
            ds = _score_delivery(delivery_days, i)
            ws = _score_warranty(warranties, i)
            pts = _score_payment(payment_terms, i)
            bfs = _score_budget_fit(o.get("total_price"), budget_max)
            rse = _score_rse(o)

            # QCDP axis scores
            qualite = round(ws, 1)                                    # Q: warranty/quality
            cout = round(ps * 0.65 + bfs * 0.35, 1)                  # C: price + budget fit
            delais = round(ds, 1)                                     # D: delivery
            performance = round(pts * 0.50 + rse * 0.50, 1)          # P: payment + RSE

            overall = round(
                qualite * QCDP_WEIGHTS["qualite"]
                + cout * QCDP_WEIGHTS["cout"]
                + delais * QCDP_WEIGHTS["delais"]
                + performance * QCDP_WEIGHTS["performance"],
                1,
            )

            scored.append(OfferScore(
                supplier_name=o.get("supplier_name", ""),
                supplier_email=o.get("supplier_email", ""),
                unit_price=o.get("unit_price"),
                total_price=o.get("total_price"),
                currency=o.get("currency", "TND"),
                delivery_days=o.get("delivery_days"),
                warranty=o.get("warranty"),
                payment_terms=o.get("payment_terms"),
                price_score=ps,
                delivery_score=ds,
                warranty_score=ws,
                payment_score=pts,
                budget_fit_score=bfs,
                rse_score=rse,
                qualite_score=qualite,
                cout_score=cout,
                delais_score=delais,
                performance_score=performance,
                overall_score=overall,
                rank=0,
                recommendation="",
            ))

        # Sort by overall score descending and assign ranks
        scored.sort(key=lambda s: s.overall_score, reverse=True)
        for rank, s in enumerate(scored, start=1):
            s.rank = rank
            s.recommendation = _generate_recommendation(s, rank, len(scored))

        best = scored[0].supplier_name if scored else None

        # Generate PDF
        report_path = None
        if generate_pdf and scored:
            from agents.agent_evaluation.tools import generate_pdf_report
            report_path = generate_pdf_report(
                product=product,
                procurement_spec=procurement_spec,
                scores=scored,
                output_dir=output_dir,
            )

        logger.info("Evaluation complete", extra={
            "best": best, "offer_count": len(scored),
        })

        return EvaluationResult(
            request_product=product,
            scores=scored,
            best_offer=best,
            report_path=report_path,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
