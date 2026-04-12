"""
One-time fix: For requests that have offers but no evaluations,
re-run the evaluation and store results to DB.

Usage:
    python fix_missing_evaluations.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)

from db.models import (
    ProcurementRequest, Offer, Evaluation, Supplier,
    get_session_factory,
)
from agents.agent_evaluation.agent import EvaluationAgent
from agents.agent_storage.agent import StorageAgent

Session = get_session_factory()
eval_agent = EvaluationAgent()
storage = StorageAgent()


def fix():
    with Session() as session:
        # Find requests with offers but no evaluations
        requests = session.query(ProcurementRequest).all()

        for req in requests:
            offer_count = session.query(Offer).filter_by(request_id=req.id).count()
            eval_count = session.query(Evaluation).filter_by(request_id=req.id).count()

            if offer_count == 0 or eval_count > 0:
                continue

            print(f"\nFixing: {req.product} (id={req.id}, offers={offer_count}, evals={eval_count})")

            # Fetch offers
            offers = session.query(Offer).filter_by(request_id=req.id).all()
            offer_dicts = []
            for o in offers:
                supplier = session.query(Supplier).filter_by(id=o.supplier_id).first()
                offer_dicts.append({
                    "supplier_name": supplier.name if supplier else "Unknown",
                    "supplier_email": supplier.email if supplier else "",
                    "unit_price": o.unit_price,
                    "total_price": o.total_price,
                    "currency": o.currency or "TND",
                    "delivery_days": o.delivery_days,
                    "warranty": o.warranty,
                    "payment_terms": o.payment_terms,
                    "notes": o.notes,
                })

            spec = {
                "product": req.product,
                "category": req.category,
                "quantity": req.quantity,
                "unit": req.unit,
                "budget_min": req.budget_min,
                "budget_max": req.budget_max,
                "deadline": req.deadline,
                "requester_email": req.requester_email,
            }

            # Run evaluation
            try:
                from dataclasses import asdict
                eval_result = eval_agent.evaluate(offer_dicts, spec)
                scores = eval_result.scores if hasattr(eval_result, "scores") else []
                if scores:
                    score_dicts = [asdict(s) if hasattr(s, "__dataclass_fields__") else s for s in scores]
                    storage.store_evaluations(
                        str(req.id), score_dicts,
                        getattr(eval_result, "report_path", None),
                    )
                    print(f"  Stored {len(score_dicts)} evaluation(s)")

                    # Update status
                    req.status = "evaluation_sent"
                    session.commit()
                    print("  Status updated to evaluation_sent")
                else:
                    print("  No scores returned from evaluation")
            except Exception as exc:
                print(f"  ERROR: {exc}")

    print("\nDone!")


if __name__ == "__main__":
    fix()
