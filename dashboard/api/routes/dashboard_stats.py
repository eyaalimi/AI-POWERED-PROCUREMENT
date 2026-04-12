"""
Dashboard overview & monthly stats endpoints.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from db.models import (
    ProcurementRequest, Supplier, Offer, Evaluation, PurchaseOrder, User,
)
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/overview")
def dashboard_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)

    req_q = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == current_user.company_id
    )
    if current_user.role == "employee":
        req_q = req_q.filter(ProcurementRequest.created_by_id == current_user.id)
    req_ids = req_q.subquery()

    total_requests = db.query(func.count(ProcurementRequest.id)).filter(
        ProcurementRequest.id.in_(req_ids)
    ).scalar() or 0

    total_this_month = db.query(func.count(ProcurementRequest.id)).filter(
        ProcurementRequest.id.in_(req_ids),
        extract("year", ProcurementRequest.created_at) == now.year,
        extract("month", ProcurementRequest.created_at) == now.month,
    ).scalar() or 0

    suppliers_found = db.query(func.count(Supplier.id)).filter(
        Supplier.request_id.in_(req_ids)
    ).scalar() or 0

    offers_received = db.query(func.count(Offer.id)).filter(
        Offer.request_id.in_(req_ids)
    ).scalar() or 0

    pending_decisions = db.query(func.count(ProcurementRequest.id)).filter(
        ProcurementRequest.id.in_(req_ids),
        ProcurementRequest.status.in_(["evaluated", "evaluation_sent", "awaiting_decision"]),
    ).scalar() or 0

    po_base = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == current_user.company_id)
    if current_user.role == "employee":
        po_base = po_base.filter(PurchaseOrder.request_id.in_(req_ids))

    awaiting_delivery = po_base.filter(
        PurchaseOrder.delivery_status.in_(["awaiting_delivery", "shipped"])
    ).count()

    delivered_this_month = po_base.filter(
        PurchaseOrder.delivery_status == "delivered",
        extract("year", PurchaseOrder.delivered_at) == now.year,
        extract("month", PurchaseOrder.delivered_at) == now.month,
    ).count()

    status_counts = dict(
        db.query(ProcurementRequest.status, func.count(ProcurementRequest.id))
        .filter(ProcurementRequest.id.in_(req_ids))
        .group_by(ProcurementRequest.status)
        .all()
    )

    return {"data": {
        "total_requests": total_requests, "total_this_month": total_this_month,
        "suppliers_found": suppliers_found, "offers_received": offers_received,
        "pending_decisions": pending_decisions, "awaiting_delivery": awaiting_delivery,
        "delivered_this_month": delivered_this_month, "status_breakdown": status_counts,
    }}


@router.get("/monthly")
def monthly_breakdown(
    month: str = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req_ids = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == current_user.company_id
    )
    if current_user.role == "employee":
        req_ids = req_ids.filter(ProcurementRequest.created_by_id == current_user.id)
    req_ids = req_ids.subquery()

    query = db.query(
        func.to_char(ProcurementRequest.created_at, "YYYY-MM").label("month"),
        func.count(ProcurementRequest.id).label("count"),
    ).filter(
        ProcurementRequest.id.in_(req_ids)
    ).group_by("month").order_by("month")

    if month:
        query = query.having(
            func.to_char(ProcurementRequest.created_at, "YYYY-MM") == month
        )

    rows = query.all()
    return {"data": [{"month": r.month, "count": r.count} for r in rows]}
