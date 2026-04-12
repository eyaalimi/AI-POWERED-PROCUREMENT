"""
Procurement request endpoints — list, detail, timeline.
"""
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, extract

from db.models import (
    ProcurementRequest, Supplier, Offer, Evaluation, PipelineEvent, User,
)
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


class NewRequestBody(BaseModel):
    product: str
    category: str = ""
    quantity: float | None = None
    unit: str = ""
    budget_min: float | None = None
    budget_max: float | None = None
    deadline: str = ""
    department: str = ""
    notes: str = ""


def _scope_request_query(query, user: User):
    query = query.filter(ProcurementRequest.company_id == user.company_id)
    if user.role == "employee":
        query = query.filter(ProcurementRequest.created_by_id == user.id)
    return query


@router.post("")
def create_request(
    body: NewRequestBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employee or admin creates a new procurement request from the dashboard."""
    req = ProcurementRequest(
        product=body.product.strip(),
        category=body.category.strip() or None,
        quantity=body.quantity,
        unit=body.unit.strip() or None,
        budget_min=body.budget_min,
        budget_max=body.budget_max,
        deadline=body.deadline.strip() or None,
        requester_email=current_user.email,
        status="pending",
        company_id=current_user.company_id,
        created_by_id=current_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # Build mailto link for Gmail notification
    subject = f"[Procurement Request] {body.product.strip()}"
    lines = [f"Product: {body.product.strip()}"]
    if body.category:
        lines.append(f"Category: {body.category}")
    if body.quantity:
        lines.append(f"Quantity: {body.quantity} {body.unit}")
    if body.budget_min or body.budget_max:
        lines.append(f"Budget: {body.budget_min or '?'} - {body.budget_max or '?'} TND")
    if body.deadline:
        lines.append(f"Deadline: {body.deadline}")
    if body.department:
        lines.append(f"Department: {body.department}")
    if body.notes:
        lines.append(f"Notes: {body.notes}")
    lines.append(f"\nRequested by: {current_user.name} ({current_user.email})")
    email_body = "\n".join(lines)

    return {
        "id": str(req.id),
        "status": "created",
        "mailto_subject": subject,
        "mailto_body": email_body,
    }


@router.get("")
def list_requests(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query(None),
    month: str = Query(None, description="YYYY-MM"),
    requester: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ProcurementRequest).order_by(desc(ProcurementRequest.created_at))
    query = _scope_request_query(query, current_user)

    if status:
        query = query.filter(ProcurementRequest.status == status)
    if requester:
        query = query.filter(ProcurementRequest.requester_email.ilike(f"%{requester}%"))
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

    data = []
    for req in requests:
        supplier_count = db.query(func.count(Supplier.id)).filter_by(request_id=req.id).scalar()
        offer_count = db.query(func.count(Offer.id)).filter_by(request_id=req.id).scalar()
        data.append({
            "id": str(req.id), "product": req.product, "category": req.category,
            "quantity": req.quantity, "unit": req.unit,
            "budget_min": req.budget_min, "budget_max": req.budget_max,
            "deadline": req.deadline, "requester_email": req.requester_email,
            "is_valid": req.is_valid, "status": req.status,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "suppliers_found": supplier_count, "offers_received": offer_count,
        })

    return {"data": data, "meta": {"total": total, "page": offset // limit + 1, "per_page": limit}}


@router.get("/{request_id}")
def get_request_detail(request_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_uuid = uuid.UUID(request_id)
    req = db.query(ProcurementRequest).filter_by(id=req_uuid, company_id=current_user.company_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if current_user.role == "employee" and req.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    suppliers = [
        {"id": str(s.id), "name": s.name, "email": s.email, "website": s.website,
         "country": s.country, "category": s.category, "relevance_score": s.relevance_score}
        for s in db.query(Supplier).filter_by(request_id=req_uuid).all()
    ]
    offers = [
        {"id": str(o.id), "supplier_id": str(o.supplier_id), "unit_price": o.unit_price,
         "total_price": o.total_price, "currency": o.currency, "delivery_days": o.delivery_days,
         "warranty": o.warranty, "payment_terms": o.payment_terms, "notes": o.notes,
         "received_at": o.received_at.isoformat() if o.received_at else None}
        for o in db.query(Offer).filter_by(request_id=req_uuid).all()
    ]
    evaluations = [
        {"id": str(e.id), "offer_id": str(e.offer_id) if e.offer_id else None,
         "supplier_name": e.supplier_name, "supplier_email": e.supplier_email,
         "qualite_score": e.qualite_score, "cout_score": e.cout_score,
         "delais_score": e.delais_score, "performance_score": e.performance_score,
         "overall_score": e.overall_score, "rank": e.rank,
         "recommendation": e.recommendation, "report_path": e.report_path,
         "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in db.query(Evaluation).filter_by(request_id=req_uuid).order_by(Evaluation.rank).all()
    ]

    return {"data": {
        "id": str(req.id), "product": req.product, "category": req.category,
        "quantity": req.quantity, "unit": req.unit,
        "budget_min": req.budget_min, "budget_max": req.budget_max,
        "deadline": req.deadline, "requester_email": req.requester_email,
        "is_valid": req.is_valid, "rejection_reason": req.rejection_reason,
        "status": req.status, "created_at": req.created_at.isoformat() if req.created_at else None,
        "suppliers": suppliers, "offers": offers, "evaluations": evaluations,
    }}


@router.get("/{request_id}/timeline")
def get_request_timeline(request_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_uuid = uuid.UUID(request_id)
    req = db.query(ProcurementRequest).filter_by(id=req_uuid, company_id=current_user.company_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    events = db.query(PipelineEvent).filter_by(request_id=req_uuid).order_by(PipelineEvent.created_at).all()
    return {"data": [
        {"id": str(e.id), "agent": e.agent, "event_type": e.event_type,
         "message": e.message, "details": e.details,
         "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in events
    ]}
