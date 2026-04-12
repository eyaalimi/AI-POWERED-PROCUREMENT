"""
dashboard/api/auth.py — Registration, login, and user info endpoints.
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt
from jose import jwt

from config import settings
from db.models import Company, User
from dashboard.api.deps import get_db, get_current_user

router = APIRouter()

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ── Schemas ──────────────────────────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    department: str = ""
    role: str = "employee"


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

@router.post("/users/create")
def create_user(body: CreateUserRequest, db: Session = Depends(get_db), admin: User = Depends(get_current_user)):
    if admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    existing = db.query(User).filter_by(email=body.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    company = db.query(Company).filter_by(id=admin.company_id).first()

    user = User(
        name=body.name.strip(),
        email=body.email.lower().strip(),
        hashed_password=hash_password(body.password),
        department=body.department.strip(),
        role=body.role if body.role in ("admin", "employee") else "employee",
        company_id=admin.company_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user_to_dict(user, company.name if company else "")


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower().strip()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    company = db.query(Company).filter_by(id=user.company_id).first()
    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "user": user_to_dict(user, company.name),
    }
