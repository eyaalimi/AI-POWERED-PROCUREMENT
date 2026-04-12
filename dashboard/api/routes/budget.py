"""
Budget dashboard endpoint — fake department data for demo.
"""
import random

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import ProcurementRequest, PurchaseOrder, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()

DEPARTMENTS = [
    {"name": "Engineering", "allocated": 250000, "color": "#6366f1"},
    {"name": "Production", "allocated": 400000, "color": "#3b82f6"},
    {"name": "Logistics", "allocated": 180000, "color": "#10b981"},
    {"name": "Quality", "allocated": 120000, "color": "#f59e0b"},
    {"name": "Maintenance", "allocated": 95000, "color": "#ef4444"},
    {"name": "R&D", "allocated": 200000, "color": "#8b5cf6"},
]

# Seed random so demo data is stable per session
random.seed(42)
FAKE_SPENT = {d["name"]: round(d["allocated"] * random.uniform(0.35, 0.85), 2) for d in DEPARTMENTS}
FAKE_PENDING = {d["name"]: round(d["allocated"] * random.uniform(0.05, 0.20), 2) for d in DEPARTMENTS}


@router.get("/budget")
def get_budget(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return budget overview per department (demo data)."""
    # Get real totals for context
    req_q = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == current_user.company_id
    )
    total_requests = req_q.count()

    real_volume = (
        db.query(func.sum(PurchaseOrder.total_price))
        .filter(PurchaseOrder.company_id == current_user.company_id, PurchaseOrder.total_price.isnot(None))
        .scalar() or 0
    )

    departments = []
    total_allocated = 0
    total_spent = 0
    total_pending = 0

    for dept in DEPARTMENTS:
        spent = FAKE_SPENT[dept["name"]]
        pending = FAKE_PENDING[dept["name"]]
        remaining = dept["allocated"] - spent - pending
        departments.append({
            "name": dept["name"],
            "color": dept["color"],
            "allocated": dept["allocated"],
            "spent": spent,
            "pending": pending,
            "remaining": round(max(remaining, 0), 2),
            "utilization": round((spent + pending) / dept["allocated"] * 100, 1),
        })
        total_allocated += dept["allocated"]
        total_spent += spent
        total_pending += pending

    # Monthly trend (fake 6 months)
    months = ["Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"]
    monthly_trend = []
    for i, m in enumerate(months):
        base = total_allocated / 12
        monthly_trend.append({
            "month": m,
            "budget": round(base, 0),
            "actual": round(base * random.uniform(0.6, 1.1), 0),
        })

    return {
        "summary": {
            "total_allocated": total_allocated,
            "total_spent": round(total_spent, 2),
            "total_pending": round(total_pending, 2),
            "total_remaining": round(total_allocated - total_spent - total_pending, 2),
            "overall_utilization": round((total_spent + total_pending) / total_allocated * 100, 1),
            "real_po_volume": round(real_volume, 2),
            "total_requests": total_requests,
        },
        "departments": departments,
        "monthly_trend": monthly_trend,
    }
