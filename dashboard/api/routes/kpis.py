"""
KPI endpoints — aggregated business metrics.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from sqlalchemy import desc

from db.models import ProcurementRequest, Offer, Evaluation, RFQ, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return aggregated KPIs for the dashboard overview."""

    # Scoped request IDs
    req_q = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == current_user.company_id
    )
    if current_user.role == "employee":
        req_q = req_q.filter(ProcurementRequest.created_by_id == current_user.id)
    req_ids = req_q.subquery()

    total_requests = db.query(func.count(ProcurementRequest.id)).filter(
        ProcurementRequest.id.in_(req_ids)
    ).scalar() or 0

    status_counts = dict(
        db.query(ProcurementRequest.status, func.count(ProcurementRequest.id))
        .filter(ProcurementRequest.id.in_(req_ids))
        .group_by(ProcurementRequest.status)
        .all()
    )

    completed = status_counts.get("evaluated", 0) + status_counts.get("completed", 0)
    success_rate = round((completed / total_requests * 100), 1) if total_requests > 0 else 0

    total_volume = (
        db.query(func.sum(Offer.total_price))
        .filter(Offer.request_id.in_(req_ids), Offer.total_price.isnot(None))
        .scalar() or 0
    )

    savings = 0.0
    best_evals = (
        db.query(Evaluation.request_id)
        .filter(Evaluation.rank == 1, Evaluation.request_id.in_(req_ids))
        .all()
    )
    for (rid,) in best_evals:
        req = db.query(ProcurementRequest).filter_by(id=rid).first()
        if req and req.budget_max:
            offer = (
                db.query(Offer).filter_by(request_id=rid)
                .filter(Offer.total_price.isnot(None))
                .order_by(Offer.total_price.asc()).first()
            )
            if offer and offer.total_price and offer.total_price < req.budget_max:
                savings += req.budget_max - offer.total_price

    avg_cycle = None
    cycle_data = (
        db.query(ProcurementRequest.created_at, func.max(Evaluation.created_at).label("eval_at"))
        .join(Evaluation, Evaluation.request_id == ProcurementRequest.id)
        .filter(ProcurementRequest.id.in_(req_ids))
        .group_by(ProcurementRequest.id, ProcurementRequest.created_at)
        .all()
    )
    if cycle_data:
        deltas = [(ec - rc).total_seconds() / 3600 for rc, ec in cycle_data if rc and ec]
        if deltas:
            avg_cycle = round(sum(deltas) / len(deltas), 1)

    total_rfqs = db.query(func.count(RFQ.id)).filter(RFQ.request_id.in_(req_ids)).scalar() or 0
    total_offers = db.query(func.count(Offer.id)).filter(Offer.request_id.in_(req_ids)).scalar() or 0

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


@router.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Top supplier recommendations — best-ranked evaluations for recent requests."""
    req_q = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == current_user.company_id
    )
    if current_user.role == "employee":
        req_q = req_q.filter(ProcurementRequest.created_by_id == current_user.id)
    req_ids = req_q.subquery()

    top_evals = (
        db.query(Evaluation)
        .filter(Evaluation.request_id.in_(req_ids), Evaluation.rank == 1)
        .order_by(desc(Evaluation.created_at))
        .limit(10)
        .all()
    )

    results = []
    for ev in top_evals:
        req = db.query(ProcurementRequest).filter_by(id=ev.request_id).first()
        results.append({
            "request_id": str(ev.request_id),
            "product": req.product if req else "Unknown",
            "supplier_name": ev.supplier_name,
            "overall_score": ev.overall_score,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        })

    return {"recommendations": results}
