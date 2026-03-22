"""
Supplier management endpoints — list, scorecard, blacklist.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from db.models import Supplier, Evaluation, Offer, RFQ, SupplierBlacklist
from dashboard.api.deps import get_db

router = APIRouter()


class BlacklistRequest(BaseModel):
    supplier_name: str
    supplier_email: str = ""
    reason: str
    blacklisted_by: str = "admin"


@router.get("")
def list_suppliers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    """List all unique suppliers with aggregated performance data."""
    # Get unique suppliers by email
    query = db.query(
        Supplier.email,
        func.max(Supplier.name).label("name"),
        func.max(Supplier.website).label("website"),
        func.max(Supplier.country).label("country"),
        func.max(Supplier.category).label("category"),
        func.avg(Supplier.relevance_score).label("avg_relevance"),
        func.count(Supplier.id).label("times_sourced"),
    ).filter(
        Supplier.email.isnot(None),
        Supplier.email != "",
    ).group_by(Supplier.email)

    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter(
            func.lower(Supplier.name).like(search_lower)
            | func.lower(Supplier.email).like(search_lower)
        )

    total = query.count()
    rows = query.offset(offset).limit(limit).all()

    # Get blacklisted emails for marking
    blacklisted = {
        b.supplier_email.lower()
        for b in db.query(SupplierBlacklist).all()
        if b.supplier_email
    }

    suppliers = []
    for row in rows:
        email = row.email

        # Performance: avg QCDP score from evaluations
        avg_score = (
            db.query(func.avg(Evaluation.overall_score))
            .filter(func.lower(Evaluation.supplier_email) == email.lower())
            .scalar()
        )

        # Response rate: offers / rfqs sent to this supplier
        rfq_count = (
            db.query(func.count(RFQ.id))
            .join(Supplier, Supplier.id == RFQ.supplier_id)
            .filter(func.lower(Supplier.email) == email.lower())
            .scalar() or 0
        )
        offer_count = (
            db.query(func.count(Offer.id))
            .join(Supplier, Supplier.id == Offer.supplier_id)
            .filter(func.lower(Supplier.email) == email.lower())
            .scalar() or 0
        )
        response_rate = round(offer_count / rfq_count * 100, 1) if rfq_count > 0 else None

        suppliers.append({
            "email": email,
            "name": row.name,
            "website": row.website,
            "country": row.country,
            "category": row.category,
            "avg_relevance_score": round(row.avg_relevance, 2) if row.avg_relevance else None,
            "avg_qcdp_score": round(avg_score, 1) if avg_score else None,
            "times_sourced": row.times_sourced,
            "rfqs_received": rfq_count,
            "offers_sent": offer_count,
            "response_rate": response_rate,
            "is_blacklisted": email.lower() in blacklisted,
        })

    return {"total": total, "suppliers": suppliers}


@router.get("/blacklist")
def get_blacklist(db: Session = Depends(get_db)):
    """Return all blacklisted suppliers."""
    entries = db.query(SupplierBlacklist).order_by(desc(SupplierBlacklist.created_at)).all()
    return {
        "blacklist": [
            {
                "id": str(b.id),
                "supplier_name": b.supplier_name,
                "supplier_email": b.supplier_email,
                "reason": b.reason,
                "blacklisted_by": b.blacklisted_by,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in entries
        ]
    }


@router.post("/blacklist")
def add_to_blacklist(req: BlacklistRequest, db: Session = Depends(get_db)):
    """Add a supplier to the blacklist."""
    entry = SupplierBlacklist(
        supplier_name=req.supplier_name,
        supplier_email=req.supplier_email or None,
        reason=req.reason,
        blacklisted_by=req.blacklisted_by,
    )
    db.add(entry)
    db.commit()
    return {"status": "blacklisted", "id": str(entry.id)}


@router.delete("/blacklist/{blacklist_id}")
def remove_from_blacklist(blacklist_id: str, db: Session = Depends(get_db)):
    """Remove a supplier from the blacklist."""
    import uuid
    deleted = db.query(SupplierBlacklist).filter_by(id=uuid.UUID(blacklist_id)).delete()
    db.commit()
    return {"status": "removed" if deleted else "not_found"}
