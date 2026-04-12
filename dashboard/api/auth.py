"""
dashboard/api/auth.py — Registration, login, and user info endpoints.
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from config import settings
from db.models import Company, User
from dashboard.api.deps import get_db

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    department: str = ""
    company_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def create_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "sub": str(user.id),
        "company_id": str(user.company_id),
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def user_to_dict(user: User, company_name: str) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "role": user.role,
        "company_id": str(user.company_id),
        "company_name": company_name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=body.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    company = db.query(Company).filter_by(name=body.company_name.strip()).first()
    if company:
        role = "employee"
    else:
        company = Company(name=body.company_name.strip())
        db.add(company)
        db.flush()
        role = "admin"

    user = User(
        name=body.name.strip(),
        email=body.email.lower().strip(),
        hashed_password=pwd_context.hash(body.password),
        department=body.department.strip(),
        role=role,
        company_id=company.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "user": user_to_dict(user, company.name),
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower().strip()).first()
    if not user or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    company = db.query(Company).filter_by(id=user.company_id).first()
    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "user": user_to_dict(user, company.name),
    }
