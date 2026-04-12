"""
Activity log endpoints — chronological event stream.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models import PipelineEvent, SourcingAuditLog, ProcurementRequest, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/activity")
def get_activity(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent: str = Query(None),
    request_id: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Scoped request IDs
    req_q = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == current_user.company_id
    )
    if current_user.role == "employee":
        req_q = req_q.filter(ProcurementRequest.created_by_id == current_user.id)
    req_ids = req_q.subquery()

    eq = db.query(PipelineEvent).filter(
        PipelineEvent.request_id.in_(req_ids)
    ).order_by(desc(PipelineEvent.created_at))
    if agent:
        eq = eq.filter(PipelineEvent.agent == agent)
    if request_id:
        eq = eq.filter(PipelineEvent.request_id == uuid.UUID(request_id))

    events = eq.offset(offset).limit(limit).all()

    results = [
        {
            "id": str(e.id),
            "request_id": str(e.request_id) if e.request_id else None,
            "agent": e.agent, "event_type": e.event_type,
            "message": e.message, "details": e.details,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

    if not agent or agent == "sourcing":
        aq = db.query(SourcingAuditLog).filter(
            SourcingAuditLog.request_id.in_(req_ids)
        ).order_by(desc(SourcingAuditLog.created_at))
        if request_id:
            aq = aq.filter(SourcingAuditLog.request_id == uuid.UUID(request_id))
        audit_entries = aq.offset(offset).limit(limit).all()

        for a in audit_entries:
            results.append({
                "id": str(a.id),
                "request_id": str(a.request_id) if a.request_id else None,
                "agent": "sourcing", "event_type": "audit",
                "message": f"{a.action}: {a.supplier_name} — {a.reason}",
                "details": f"email={a.supplier_email}, score={a.relevance_score}, source={a.source}",
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })

    results.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return {"total": len(results), "events": results[:limit]}
