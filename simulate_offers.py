"""
Inject simulated supplier offers + evaluations into the DB for testing.

Usage:
    python simulate_offers.py                  # inject for ALL requests missing offers
    python simulate_offers.py <request_id>     # inject for a specific request
"""
import sys
import uuid
import random
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)

from db.models import (
    ProcurementRequest, Supplier, RFQ, Offer, Evaluation,
    get_session_factory,
)

Session = get_session_factory()

# ── Fake supplier data ──────────────────────────────────────────────────────

FAKE_SUPPLIERS = [
    {"name": "TechnoPlus SARL",   "email": "contact@technoplus.tn",   "country": "Tunisia", "website": "https://technoplus.tn"},
    {"name": "MegaSupply Co.",     "email": "sales@megasupply.com",    "country": "France",  "website": "https://megasupply.com"},
    {"name": "ProEquip Tunisia",   "email": "info@proequip.tn",       "country": "Tunisia", "website": "https://proequip.tn"},
]


def inject_for_request(session, req):
    """Create 3 fake suppliers, offers, and evaluations for a request."""
    print(f"\n{'='*60}")
    print(f"Request: {req.product} (id={req.id})")
    print(f"  Current status: {req.status}")

    # Check existing
    existing_offers = session.query(Offer).filter_by(request_id=req.id).count()
    existing_evals = session.query(Evaluation).filter_by(request_id=req.id).count()
    print(f"  Existing offers: {existing_offers}, evaluations: {existing_evals}")

    if existing_evals > 0:
        print("  -> Already has evaluations, skipping.")
        return

    budget_min = req.budget_min or 50
    budget_max = req.budget_max or 500
    qty = req.quantity or 10

    evaluations = []

    for i, sup_data in enumerate(FAKE_SUPPLIERS):
        # ── Supplier ────────────────────────────────────────────────────
        supplier = session.query(Supplier).filter_by(
            request_id=req.id, email=sup_data["email"]
        ).first()

        if not supplier:
            supplier = Supplier(
                request_id=req.id,
                name=sup_data["name"],
                email=sup_data["email"],
                country=sup_data["country"],
                website=sup_data["website"],
                category=req.category or "General",
                relevance_score=round(random.uniform(0.7, 1.0), 2),
            )
            session.add(supplier)
            session.flush()
            print(f"  + Supplier: {supplier.name}")

        # ── RFQ ─────────────────────────────────────────────────────────
        rfq = session.query(RFQ).filter_by(
            request_id=req.id, supplier_id=supplier.id
        ).first()

        if not rfq:
            rfq = RFQ(
                request_id=req.id,
                supplier_id=supplier.id,
                subject=f"RFQ - {req.product}",
                status="sent",
            )
            session.add(rfq)
            session.flush()

        # ── Offer ───────────────────────────────────────────────────────
        existing_offer = session.query(Offer).filter_by(
            request_id=req.id, supplier_id=supplier.id
        ).first()

        if not existing_offer:
            unit_price = round(random.uniform(budget_min * 0.6, budget_max * 1.1) / qty, 2)
            total_price = round(unit_price * qty, 2)
            offer = Offer(
                request_id=req.id,
                supplier_id=supplier.id,
                rfq_id=rfq.id,
                unit_price=unit_price,
                total_price=total_price,
                currency="TND",
                delivery_days=random.randint(3, 21),
                warranty=random.choice(["6 months", "1 year", "2 years", "No warranty"]),
                payment_terms=random.choice(["30 days net", "50% advance", "On delivery", "60 days net"]),
                notes=f"Simulated offer for {req.product}",
                received_at=datetime.now(timezone.utc),
            )
            session.add(offer)
            session.flush()
            print(f"  + Offer: {supplier.name} -> {total_price} TND")
        else:
            offer = existing_offer

        # ── Evaluation scores ───────────────────────────────────────────
        qualite = round(random.uniform(55, 95), 1)
        cout = round(random.uniform(50, 95), 1)
        delais = round(random.uniform(40, 95), 1)
        perf = round(random.uniform(50, 95), 1)
        overall = round(qualite * 0.3 + cout * 0.3 + delais * 0.2 + perf * 0.2, 1)

        evaluations.append({
            "supplier_name": supplier.name,
            "supplier_email": supplier.email,
            "offer_id": offer.id,
            "qualite_score": qualite,
            "cout_score": cout,
            "delais_score": delais,
            "performance_score": perf,
            "overall_score": overall,
            "price_score": cout,
            "delivery_score": delais,
            "warranty_score": round(random.uniform(50, 90), 1),
            "payment_score": round(random.uniform(50, 90), 1),
            "budget_fit_score": round(random.uniform(60, 95), 1),
            "recommendation": random.choice([
                "Strong candidate with competitive pricing and reliable delivery.",
                "Good overall value. Consider for budget-conscious procurement.",
                "Decent option but delivery times could be improved.",
            ]),
        })

    # Rank by overall score
    evaluations.sort(key=lambda e: e["overall_score"], reverse=True)
    for rank, ev in enumerate(evaluations, 1):
        ev["rank"] = rank

    # ── Store evaluations ───────────────────────────────────────────────
    for ev in evaluations:
        eval_record = Evaluation(
            request_id=req.id,
            offer_id=ev.get("offer_id"),
            supplier_name=ev["supplier_name"],
            supplier_email=ev["supplier_email"],
            price_score=ev.get("price_score"),
            delivery_score=ev.get("delivery_score"),
            warranty_score=ev.get("warranty_score"),
            payment_score=ev.get("payment_score"),
            budget_fit_score=ev.get("budget_fit_score"),
            qualite_score=ev.get("qualite_score"),
            cout_score=ev.get("cout_score"),
            delais_score=ev.get("delais_score"),
            performance_score=ev.get("performance_score"),
            overall_score=ev.get("overall_score"),
            rank=ev["rank"],
            recommendation=ev.get("recommendation"),
        )
        session.add(eval_record)

    # Update request status
    req.status = "evaluation_sent"
    session.commit()

    print(f"  + {len(evaluations)} evaluations stored")
    print("  -> Status updated to: evaluation_sent")


def main():
    target_id = sys.argv[1] if len(sys.argv) > 1 else None

    with Session() as session:
        if target_id:
            req = session.query(ProcurementRequest).filter_by(
                id=uuid.UUID(target_id)
            ).first()
            if not req:
                print(f"Request {target_id} not found.")
                return
            inject_for_request(session, req)
        else:
            requests = session.query(ProcurementRequest).all()
            if not requests:
                print("No requests found in DB.")
                return
            print(f"Found {len(requests)} request(s)")
            for req in requests:
                inject_for_request(session, req)

    print("\nDone! Refresh the dashboard to see the data.")


if __name__ == "__main__":
    main()
