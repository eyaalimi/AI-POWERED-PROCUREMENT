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

from dashboard.api.routes import kpis, pipelines, activity, suppliers, evaluations

app = FastAPI(
    title="Procurement AI Dashboard",
    version="1.0.0",
    description="Monitoring dashboard for the autonomous procurement pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpis.router, prefix="/api/dashboard", tags=["KPIs"])
app.include_router(pipelines.router, prefix="/api/dashboard", tags=["Pipelines"])
app.include_router(activity.router, prefix="/api/dashboard", tags=["Activity"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
