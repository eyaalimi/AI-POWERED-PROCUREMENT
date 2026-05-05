"""
Email inbox endpoints — view procurement request emails.
"""
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, extract

from db.models import ProcurementRequest, PipelineEvent, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


def _scope(query, user: User):
    query = query.filter(ProcurementRequest.company_id == user.company_id)
    if user.role == "employee":
        query = query.filter(ProcurementRequest.created_by_id == user.id)
    return query


@router.get("/inbox")
def get_inbox(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    month: str = Query(None, description="YYYY-MM"),
    status: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ProcurementRequest).order_by(desc(ProcurementRequest.created_at))
    query = _scope(query, current_user)

    if status:
        query = query.filter(ProcurementRequest.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter(
            ProcurementRequest.product.ilike(s)
            | ProcurementRequest.requester_email.ilike(s)
            | ProcurementRequest.category.ilike(s)
        )
    if month:
        try:
            year, mon = month.split("-")
            query = query.filter(
                extract("year", ProcurementRequest.created_at) == int(year),
                extract("month", ProcurementRequest.created_at) == int(mon),
            )
        except ValueError:
            pass

    total = query.count()
    requests = query.offset(offset).limit(limit).all()

    return {
        "data": [
            {
                "id": str(req.id), "requester_email": req.requester_email,
                "product": req.product, "category": req.category,
                "quantity": req.quantity, "unit": req.unit,
                "budget_min": req.budget_min, "budget_max": req.budget_max,
                "deadline": req.deadline, "is_valid": req.is_valid,
                "rejection_reason": req.rejection_reason, "status": req.status,
                "created_at": req.created_at.isoformat() if req.created_at else None,
            }
            for req in requests
        ],
        "meta": {"total": total, "page": offset // limit + 1, "per_page": limit},
    }


@router.get("/{email_id}")
def get_email_detail(email_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_uuid = uuid.UUID(email_id)
    req = db.query(ProcurementRequest).filter_by(id=req_uuid, company_id=current_user.company_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Not found")

    analysis_events = db.query(PipelineEvent).filter_by(request_id=req_uuid, agent="analysis").order_by(PipelineEvent.created_at).all()
    all_events = db.query(PipelineEvent).filter_by(request_id=req_uuid).order_by(PipelineEvent.created_at).all()

    return {"data": {
        "id": str(req.id), "requester_email": req.requester_email,
        "product": req.product, "category": req.category,
        "quantity": req.quantity, "unit": req.unit,
        "budget_min": req.budget_min, "budget_max": req.budget_max,
        "deadline": req.deadline, "is_valid": req.is_valid,
        "rejection_reason": req.rejection_reason, "status": req.status,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "analysis": [
            {"agent": e.agent, "event_type": e.event_type, "message": e.message,
             "details": e.details, "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in analysis_events
        ],
        "timeline": [
            {"agent": e.agent, "event_type": e.event_type, "message": e.message,
             "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in all_events
        ],
    }}
