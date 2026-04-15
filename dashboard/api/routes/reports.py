"""
RFQ Reports endpoint — lists evaluation PDF reports from S3/local storage.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models import Evaluation, ProcurementRequest, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req_ids = db.query(ProcurementRequest.id).filter(
        ProcurementRequest.company_id == current_user.company_id
    )
    if current_user.role == "employee":
        req_ids = req_ids.filter(
            ProcurementRequest.created_by_id == current_user.id
        )
    req_ids = req_ids.subquery()

    evals_with_reports = (
        db.query(Evaluation)
        .filter(
            Evaluation.request_id.in_(req_ids),
            Evaluation.report_path.isnot(None),
            Evaluation.rank == 1,
        )
        .order_by(desc(Evaluation.created_at))
        .all()
    )

    seen_requests = set()
    reports = []
    for ev in evals_with_reports:
        rid = str(ev.request_id)
        if rid in seen_requests:
            continue
        seen_requests.add(rid)

        req = db.query(ProcurementRequest).filter_by(id=ev.request_id).first()
        reports.append({
            "request_id": rid,
            "product": req.product if req else "Unknown",
            "status": req.status if req else "unknown",
            "report_path": ev.report_path,
            "supplier_name": ev.supplier_name,
            "overall_score": ev.overall_score,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        })

    return {
        "total": len(reports),
        "reports": reports,
    }
