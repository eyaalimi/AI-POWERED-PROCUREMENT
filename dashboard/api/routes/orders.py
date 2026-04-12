"""
Purchase order & delivery tracking endpoints.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, extract

from db.models import ProcurementRequest, Evaluation, Offer, PurchaseOrder, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


class CreatePORequest(BaseModel):
    evaluation_id: str
    quantity: float | None = None
    delivery_address: str = ""
    cost_center: str = ""
    department: str = ""
    requester_name: str = ""
    notes: str = ""


class UpdateStatusRequest(BaseModel):
    delivery_status: str


class ConfirmDeliveryRequest(BaseModel):
    confirmed_by: str


def _generate_po_reference(db: Session) -> str:
    now = datetime.now(timezone.utc)
    prefix = f"PO-{now.year}-{now.month:02d}"
    count = (
        db.query(func.count(PurchaseOrder.id))
        .filter(PurchaseOrder.po_reference.like(f"{prefix}%"))
        .scalar() or 0
    )
    return f"{prefix}-{count + 1:04d}"


def _po_to_dict(po: PurchaseOrder) -> dict:
    return {
        "id": str(po.id), "request_id": str(po.request_id),
        "evaluation_id": str(po.evaluation_id), "po_reference": po.po_reference,
        "supplier_name": po.supplier_name, "supplier_email": po.supplier_email,
        "product": po.product, "quantity": po.quantity, "unit": po.unit,
        "unit_price": po.unit_price, "total_price": po.total_price, "currency": po.currency,
        "delivery_address": po.delivery_address, "cost_center": po.cost_center,
        "department": po.department, "requester_name": po.requester_name,
        "requester_email": po.requester_email, "notes": po.notes,
        "delivery_status": po.delivery_status,
        "delivered_at": po.delivered_at.isoformat() if po.delivered_at else None,
        "confirmed_by": po.confirmed_by,
        "created_at": po.created_at.isoformat() if po.created_at else None,
        "updated_at": po.updated_at.isoformat() if po.updated_at else None,
    }


@router.post("/requests/{request_id}/purchase-order")
def create_purchase_order(request_id: str, body: CreatePORequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_uuid = uuid.UUID(request_id)
    eval_uuid = uuid.UUID(body.evaluation_id)

    req = db.query(ProcurementRequest).filter_by(id=req_uuid, company_id=current_user.company_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    evaluation = db.query(Evaluation).filter_by(id=eval_uuid, request_id=req_uuid).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    existing = db.query(PurchaseOrder).filter_by(request_id=req_uuid).first()
    if existing:
        raise HTTPException(status_code=409, detail="Purchase order already exists for this request")

    offer = db.query(Offer).filter_by(id=evaluation.offer_id).first() if evaluation.offer_id else None

    po = PurchaseOrder(
        request_id=req_uuid, evaluation_id=eval_uuid,
        po_reference=_generate_po_reference(db),
        supplier_name=evaluation.supplier_name, supplier_email=evaluation.supplier_email,
        product=req.product, quantity=body.quantity or req.quantity, unit=req.unit,
        unit_price=offer.unit_price if offer else None,
        total_price=offer.total_price if offer else None,
        currency=offer.currency if offer else "TND",
        delivery_address=body.delivery_address, cost_center=body.cost_center,
        department=body.department, requester_name=body.requester_name,
        requester_email=req.requester_email, notes=body.notes,
        company_id=current_user.company_id,
    )
    db.add(po)
    req.status = "po_generated"
    db.commit()
    db.refresh(po)
    return {"data": _po_to_dict(po)}


@router.get("/requests/{request_id}/purchase-order")
def get_request_po(request_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_uuid = uuid.UUID(request_id)
    po = db.query(PurchaseOrder).filter_by(request_id=req_uuid, company_id=current_user.company_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="No purchase order found")
    return {"data": _po_to_dict(po)}


@router.get("")
def list_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    delivery_status: str = Query(None),
    month: str = Query(None, description="YYYY-MM"),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PurchaseOrder).filter(
        PurchaseOrder.company_id == current_user.company_id
    ).order_by(desc(PurchaseOrder.created_at))

    if current_user.role == "employee":
        user_req_ids = db.query(ProcurementRequest.id).filter(
            ProcurementRequest.created_by_id == current_user.id
        ).subquery()
        query = query.filter(PurchaseOrder.request_id.in_(user_req_ids))

    if delivery_status:
        query = query.filter(PurchaseOrder.delivery_status == delivery_status)
    if search:
        s = f"%{search}%"
        query = query.filter(
            PurchaseOrder.po_reference.ilike(s) | PurchaseOrder.product.ilike(s)
            | PurchaseOrder.supplier_name.ilike(s) | PurchaseOrder.requester_email.ilike(s)
        )
    if month:
        try:
            year, mon = month.split("-")
            query = query.filter(
                extract("year", PurchaseOrder.created_at) == int(year),
                extract("month", PurchaseOrder.created_at) == int(mon),
            )
        except ValueError:
            pass

    total = query.count()
    orders = query.offset(offset).limit(limit).all()
    return {"data": [_po_to_dict(po) for po in orders], "meta": {"total": total, "page": offset // limit + 1, "per_page": limit}}


@router.get("/stats")
def order_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    base = db.query(PurchaseOrder).filter(PurchaseOrder.company_id == current_user.company_id)
    if current_user.role == "employee":
        user_req_ids = db.query(ProcurementRequest.id).filter(
            ProcurementRequest.created_by_id == current_user.id
        ).subquery()
        base = base.filter(PurchaseOrder.request_id.in_(user_req_ids))

    total = base.count()
    awaiting = base.filter(PurchaseOrder.delivery_status.in_(["awaiting_delivery", "shipped"])).count()
    delivered_this_month = base.filter(
        PurchaseOrder.delivery_status == "delivered",
        extract("year", PurchaseOrder.delivered_at) == now.year,
        extract("month", PurchaseOrder.delivered_at) == now.month,
    ).count()

    avg_delivery = (
        base.filter(PurchaseOrder.delivered_at.isnot(None))
        .with_entities(func.avg(func.extract("epoch", PurchaseOrder.delivered_at - PurchaseOrder.created_at) / 86400))
        .scalar()
    )

    return {"data": {
        "total_orders": total, "active_orders": awaiting,
        "delivered_this_month": delivered_this_month,
        "avg_delivery_days": round(avg_delivery, 1) if avg_delivery else None,
    }}


@router.get("/{po_id}")
def get_order(po_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter_by(id=uuid.UUID(po_id), company_id=current_user.company_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"data": _po_to_dict(po)}


@router.patch("/{po_id}/status")
def update_order_status(po_id: str, body: UpdateStatusRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    valid = ["awaiting_delivery", "shipped", "delivered", "cancelled"]
    if body.delivery_status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    po = db.query(PurchaseOrder).filter_by(id=uuid.UUID(po_id), company_id=current_user.company_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Order not found")

    po.delivery_status = body.delivery_status
    if body.delivery_status == "delivered":
        po.delivered_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(po)
    return {"data": _po_to_dict(po)}


@router.post("/{po_id}/confirm-delivery")
def confirm_delivery(po_id: str, body: ConfirmDeliveryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    po = db.query(PurchaseOrder).filter_by(id=uuid.UUID(po_id), company_id=current_user.company_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Order not found")

    po.delivery_status = "delivered"
    po.delivered_at = datetime.now(timezone.utc)
    po.confirmed_by = body.confirmed_by
    db.commit()

    req = db.query(ProcurementRequest).filter_by(id=po.request_id).first()
    if req:
        req.status = "completed"
        db.commit()

    db.refresh(po)
    return {"data": _po_to_dict(po)}
