"""
Export endpoints — CSV downloads for requests, suppliers, orders.
"""
import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from db.models import (
    ProcurementRequest, Supplier, Evaluation, PurchaseOrder, User,
)
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


def _stream_csv(rows: list[dict], filename: str) -> StreamingResponse:
    if not rows:
        rows = [{"info": "No data"}]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _scoped_request_ids(db: Session, user: User):
    q = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == user.company_id
    )
    if user.role == "employee":
        q = q.filter(ProcurementRequest.created_by_id == user.id)
    return q.subquery()


@router.get("/requests")
def export_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_ids = _scoped_request_ids(db, current_user)
    requests = (
        db.query(ProcurementRequest)
        .filter(ProcurementRequest.id.in_(req_ids))
        .order_by(desc(ProcurementRequest.created_at))
        .all()
    )
    rows = [
        {
            "Product": r.product,
            "Category": r.category or "",
            "Quantity": r.quantity or "",
            "Unit": r.unit or "",
            "Budget Min": r.budget_min or "",
            "Budget Max": r.budget_max or "",
            "Deadline": r.deadline or "",
            "Requester": r.requester_email,
            "Status": r.status,
            "Valid": "Yes" if r.is_valid else "No",
            "Created At": r.created_at.isoformat() if r.created_at else "",
        }
        for r in requests
    ]
    return _stream_csv(rows, "procurement_requests.csv")


@router.get("/suppliers")
def export_suppliers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_ids = _scoped_request_ids(db, current_user)
    suppliers = (
        db.query(
            Supplier.email,
            func.max(Supplier.name).label("name"),
            func.max(Supplier.website).label("website"),
            func.max(Supplier.country).label("country"),
            func.max(Supplier.category).label("category"),
            func.avg(Supplier.relevance_score).label("avg_relevance"),
            func.count(Supplier.id).label("times_sourced"),
        )
        .filter(Supplier.email.isnot(None), Supplier.email != "", Supplier.request_id.in_(req_ids))
        .group_by(Supplier.email)
        .all()
    )
    rows = []
    for s in suppliers:
        avg_score = (
            db.query(func.avg(Evaluation.overall_score))
            .filter(func.lower(Evaluation.supplier_email) == s.email.lower())
            .filter(Evaluation.request_id.in_(req_ids))
            .scalar()
        )
        rows.append({
            "Name": s.name,
            "Email": s.email,
            "Website": s.website or "",
            "Country": s.country or "",
            "Category": s.category or "",
            "Avg Relevance": round(s.avg_relevance, 2) if s.avg_relevance else "",
            "Avg QCDP Score": round(avg_score, 1) if avg_score else "",
            "Times Sourced": s.times_sourced,
        })
    return _stream_csv(rows, "suppliers.csv")


@router.get("/orders")
def export_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(PurchaseOrder).filter(
        PurchaseOrder.company_id == current_user.company_id
    ).order_by(desc(PurchaseOrder.created_at))

    if current_user.role == "employee":
        user_req_ids = db.query(ProcurementRequest.id).filter(
            ProcurementRequest.created_by_id == current_user.id
        ).subquery()
        query = query.filter(PurchaseOrder.request_id.in_(user_req_ids))

    orders = query.all()
    rows = [
        {
            "PO Reference": po.po_reference,
            "Product": po.product,
            "Supplier": po.supplier_name,
            "Supplier Email": po.supplier_email or "",
            "Quantity": po.quantity or "",
            "Unit": po.unit or "",
            "Unit Price": po.unit_price or "",
            "Total Price": po.total_price or "",
            "Currency": po.currency or "",
            "Department": po.department or "",
            "Requester": po.requester_email or "",
            "Status": po.delivery_status,
            "Created At": po.created_at.isoformat() if po.created_at else "",
            "Delivered At": po.delivered_at.isoformat() if po.delivered_at else "",
        }
        for po in orders
    ]
    return _stream_csv(rows, "purchase_orders.csv")
