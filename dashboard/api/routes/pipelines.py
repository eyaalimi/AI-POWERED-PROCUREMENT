"""
Pipeline endpoints — live view of procurement requests and their stages.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models import (
    ProcurementRequest, Supplier, RFQ, Offer, Evaluation, PipelineEvent,
)
from dashboard.api.deps import get_db

router = APIRouter()

# Map DB status to pipeline stage progression
STAGE_ORDER = [
    "pending", "analyzing", "sourcing", "rfqs_sent",
    "offers_received", "evaluated", "completed",
]


def _stage_status(current_status: str, stage: str) -> str:
    """Return 'done', 'active', or 'pending' for a given stage."""
    if current_status in ("rejected", "failed"):
        return "error" if stage == "analyzing" else "skipped"
    current_idx = STAGE_ORDER.index(current_status) if current_status in STAGE_ORDER else -1
    stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else -1
    if stage_idx < current_idx:
        return "done"
    elif stage_idx == current_idx:
        return "active"
    return "pending"


@router.get("/pipelines")
def get_pipelines(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """Return procurement pipelines with stage-by-stage status."""
    query = db.query(ProcurementRequest).order_by(desc(ProcurementRequest.created_at))

    if status:
        query = query.filter(ProcurementRequest.status == status)

    total = query.count()
    requests = query.offset(offset).limit(limit).all()

    results = []
    for req in requests:
        supplier_count = db.query(Supplier).filter_by(request_id=req.id).count()
        rfq_count = db.query(RFQ).filter_by(request_id=req.id).count()
        offer_count = db.query(Offer).filter_by(request_id=req.id).count()
        eval_count = db.query(Evaluation).filter_by(request_id=req.id).count()

        best_eval = (
            db.query(Evaluation)
            .filter_by(request_id=req.id, rank=1)
            .first()
        )

        stages = {
            "analysis": _stage_status(req.status, "analyzing"),
            "sourcing": _stage_status(req.status, "sourcing"),
            "rfqs": _stage_status(req.status, "rfqs_sent"),
            "offers": _stage_status(req.status, "offers_received"),
            "evaluation": _stage_status(req.status, "evaluated"),
        }

        results.append({
            "id": str(req.id),
            "product": req.product,
            "category": req.category,
            "requester_email": req.requester_email,
            "status": req.status,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "budget_max": req.budget_max,
            "deadline": req.deadline,
            "stages": stages,
            "suppliers_found": supplier_count,
            "rfqs_sent": rfq_count,
            "offers_received": offer_count,
            "evaluations": eval_count,
            "best_offer": {
                "supplier_name": best_eval.supplier_name,
                "overall_score": best_eval.overall_score,
                "supplier_email": best_eval.supplier_email,
            } if best_eval else None,
        })

    return {"total": total, "pipelines": results}


@router.get("/pipelines/{request_id}")
def get_pipeline_detail(request_id: str, db: Session = Depends(get_db)):
    """Return detailed view of a single pipeline run."""
    import uuid
    req_uuid = uuid.UUID(request_id)

    req = db.query(ProcurementRequest).filter_by(id=req_uuid).first()
    if not req:
        return {"error": "Not found"}

    suppliers = [
        {
            "name": s.name, "email": s.email, "website": s.website,
            "category": s.category, "relevance_score": s.relevance_score,
        }
        for s in db.query(Supplier).filter_by(request_id=req_uuid).all()
    ]

    rfqs = [
        {
            "supplier_id": str(r.supplier_id), "subject": r.subject,
            "status": r.status, "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            "reminder_sent": r.reminder_sent,
        }
        for r in db.query(RFQ).filter_by(request_id=req_uuid).all()
    ]

    offers = [
        {
            "supplier_id": str(o.supplier_id),
            "unit_price": o.unit_price, "total_price": o.total_price,
            "currency": o.currency, "delivery_days": o.delivery_days,
            "warranty": o.warranty, "payment_terms": o.payment_terms,
        }
        for o in db.query(Offer).filter_by(request_id=req_uuid).all()
    ]

    evaluations = [
        {
            "supplier_name": e.supplier_name, "supplier_email": e.supplier_email,
            "qualite_score": e.qualite_score, "cout_score": e.cout_score,
            "delais_score": e.delais_score, "performance_score": e.performance_score,
            "overall_score": e.overall_score, "rank": e.rank,
            "recommendation": e.recommendation, "report_path": e.report_path,
        }
        for e in db.query(Evaluation).filter_by(request_id=req_uuid).order_by(Evaluation.rank).all()
    ]

    events = [
        {
            "agent": ev.agent, "event_type": ev.event_type,
            "message": ev.message, "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }
        for ev in db.query(PipelineEvent).filter_by(request_id=req_uuid).order_by(PipelineEvent.created_at).all()
    ]

    return {
        "request": {
            "id": str(req.id), "product": req.product, "category": req.category,
            "quantity": req.quantity, "unit": req.unit,
            "budget_min": req.budget_min, "budget_max": req.budget_max,
            "deadline": req.deadline, "requester_email": req.requester_email,
            "status": req.status, "is_valid": req.is_valid,
            "rejection_reason": req.rejection_reason,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        },
        "suppliers": suppliers,
        "rfqs": rfqs,
        "offers": offers,
        "evaluations": evaluations,
        "events": events,
    }
