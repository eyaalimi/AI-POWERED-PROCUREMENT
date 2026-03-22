"""
KPI endpoints — aggregated business metrics.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import ProcurementRequest, Offer, Evaluation, RFQ
from dashboard.api.deps import get_db

router = APIRouter()


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)):
    """Return aggregated KPIs for the dashboard overview."""

    # Total requests
    total_requests = db.query(func.count(ProcurementRequest.id)).scalar() or 0

    # Requests by status
    status_counts = dict(
        db.query(ProcurementRequest.status, func.count(ProcurementRequest.id))
        .group_by(ProcurementRequest.status)
        .all()
    )

    completed = status_counts.get("evaluated", 0) + status_counts.get("completed", 0)
    success_rate = round((completed / total_requests * 100), 1) if total_requests > 0 else 0

    # Total procurement volume (sum of all offer prices)
    total_volume = (
        db.query(func.sum(Offer.total_price))
        .filter(Offer.total_price.isnot(None))
        .scalar() or 0
    )

    # Savings: for each rank-1 evaluation, compare best offer vs budget_max
    savings = 0.0
    best_evals = (
        db.query(Evaluation.request_id)
        .filter(Evaluation.rank == 1)
        .all()
    )
    for (req_id,) in best_evals:
        req = db.query(ProcurementRequest).filter_by(id=req_id).first()
        if req and req.budget_max:
            offer = (
                db.query(Offer)
                .filter_by(request_id=req_id)
                .filter(Offer.total_price.isnot(None))
                .order_by(Offer.total_price.asc())
                .first()
            )
            if offer and offer.total_price and offer.total_price < req.budget_max:
                savings += req.budget_max - offer.total_price

    # Average cycle time (created_at to latest evaluation created_at)
    avg_cycle = None
    cycle_data = (
        db.query(
            ProcurementRequest.created_at,
            func.max(Evaluation.created_at).label("eval_at"),
        )
        .join(Evaluation, Evaluation.request_id == ProcurementRequest.id)
        .group_by(ProcurementRequest.id, ProcurementRequest.created_at)
        .all()
    )
    if cycle_data:
        deltas = []
        for req_created, eval_created in cycle_data:
            if req_created and eval_created:
                delta = (eval_created - req_created).total_seconds() / 3600
                deltas.append(delta)
        if deltas:
            avg_cycle = round(sum(deltas) / len(deltas), 1)

    # RFQ stats
    total_rfqs = db.query(func.count(RFQ.id)).scalar() or 0
    total_offers = db.query(func.count(Offer.id)).scalar() or 0

    return {
        "total_requests": total_requests,
        "status_breakdown": status_counts,
        "completed": completed,
        "success_rate": success_rate,
        "total_volume_tnd": round(total_volume, 2),
        "savings_tnd": round(savings, 2),
        "avg_cycle_hours": avg_cycle,
        "total_rfqs_sent": total_rfqs,
        "total_offers_received": total_offers,
    }
