"""
dashboard/api/main.py — FastAPI backend for the Procurement Dashboard.

Run with:
    uvicorn dashboard.api.main:app --reload --port 8000
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends

from dashboard.api.auth import router as auth_router, user_to_dict
from dashboard.api.deps import get_current_user, get_db
from dashboard.api.routes import (
    kpis, pipelines, activity, suppliers, evaluations,
    requests, emails, orders, dashboard_stats, budget, export, reports,
)

app = FastAPI(
    title="Procurement AI Dashboard",
    version="1.0.0",
    description="Monitoring dashboard for the autonomous procurement pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://procurement-ai.click",
        "https://www.procurement-ai.click",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(kpis.router, prefix="/api/dashboard", tags=["KPIs"])
app.include_router(pipelines.router, prefix="/api/dashboard", tags=["Pipelines"])
app.include_router(activity.router, prefix="/api/dashboard", tags=["Activity"])
app.include_router(dashboard_stats.router, prefix="/api/dashboard", tags=["Dashboard Stats"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(requests.router, prefix="/api/requests", tags=["Requests"])
app.include_router(emails.router, prefix="/api/emails", tags=["Emails"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(budget.router, prefix="/api/dashboard", tags=["Budget"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(reports.router, prefix="/api/dashboard", tags=["Reports"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/auth/users", tags=["Auth"])
def list_users(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    from db.models import Company, User
    if current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(User).filter_by(company_id=current_user.company_id).order_by(User.created_at).all()
    company = db.query(Company).filter_by(id=current_user.company_id).first()
    company_name = company.name if company else ""
    return [user_to_dict(u, company_name) for u in users]


@app.get("/api/auth/me", tags=["Auth"])
def get_me(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    from db.models import Company
    company = db.query(Company).filter_by(id=current_user.company_id).first()
    return user_to_dict(current_user, company.name if company else "")


# ── Lambda handler (via Mangum) ──────────────────────────────────────────────
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None  # local dev — Mangum not needed
