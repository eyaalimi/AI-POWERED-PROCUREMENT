"""
Evaluation endpoints — QCDP details per request.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.models import Evaluation, ProcurementRequest, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()


@router.get("/{request_id}")
def get_evaluations(request_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req_uuid = uuid.UUID(request_id)
    req = db.query(ProcurementRequest).filter_by(id=req_uuid, company_id=current_user.company_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    evals = db.query(Evaluation).filter_by(request_id=req_uuid).order_by(Evaluation.rank).all()

    return {
        "request_id": request_id,
        "evaluations": [
            {
                "id": str(e.id), "supplier_name": e.supplier_name,
                "supplier_email": e.supplier_email,
                "price_score": e.price_score, "delivery_score": e.delivery_score,
                "warranty_score": e.warranty_score, "payment_score": e.payment_score,
                "budget_fit_score": e.budget_fit_score, "rse_score": e.rse_score,
                "qualite_score": e.qualite_score, "cout_score": e.cout_score,
                "delais_score": e.delais_score, "performance_score": e.performance_score,
                "overall_score": e.overall_score, "rank": e.rank,
                "recommendation": e.recommendation, "report_path": e.report_path,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in evals
        ],
    }
