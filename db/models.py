"""
db/models.py — SQLAlchemy ORM models for the procurement database.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey,
    create_engine, Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

from config import settings

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


# ── Auth Tables ──────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    employee = "employee"


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    users = relationship("User", back_populates="company")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    department = Column(String(100))
    role = Column(String(20), default="employee")
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship("Company", back_populates="users")


# ── Tables ───────────────────────────────────────────────────────────────────

class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product = Column(Text, nullable=False)
    category = Column(String(100))
    quantity = Column(Float)
    unit = Column(String(50))
    budget_min = Column(Float)
    budget_max = Column(Float)
    deadline = Column(String(20))
    requester_email = Column(String(255), nullable=False)
    is_valid = Column(Boolean, default=True)
    rejection_reason = Column(Text)
    status = Column(String(50), default="pending")
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    suppliers = relationship("Supplier", back_populates="request", cascade="all, delete-orphan")
    rfqs = relationship("RFQ", back_populates="request", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="request", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="request", cascade="all, delete-orphan")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False)
    name = Column(String(255), nullable=False)
    website = Column(Text)
    email = Column(String(255))
    country = Column(String(100))
    category = Column(String(100))
    relevance_score = Column(Float)
    source_url = Column(Text)

    request = relationship("ProcurementRequest", back_populates="suppliers")
    rfqs = relationship("RFQ", back_populates="supplier", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="supplier", cascade="all, delete-orphan")


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    subject = Column(String(500))
    message_id = Column(String(500))
    status = Column(String(50), nullable=False)
    sent_at = Column(DateTime(timezone=True), default=utcnow)
    reminder_sent = Column(Boolean, default=False)
    reminder_at = Column(DateTime(timezone=True))

    request = relationship("ProcurementRequest", back_populates="rfqs")
    supplier = relationship("Supplier", back_populates="rfqs")
    offers = relationship("Offer", back_populates="rfq", cascade="all, delete-orphan")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id"), nullable=False)
    unit_price = Column(Float)
    total_price = Column(Float)
    currency = Column(String(10), default="TND")
    delivery_days = Column(Integer)
    warranty = Column(Text)
    payment_terms = Column(Text)
    notes = Column(Text)
    raw_body = Column(Text)
    has_pdf = Column(Boolean, default=False)
    received_at = Column(DateTime(timezone=True), default=utcnow)

    request = relationship("ProcurementRequest", back_populates="offers")
    supplier = relationship("Supplier", back_populates="offers")
    rfq = relationship("RFQ", back_populates="offers")
    evaluation = relationship("Evaluation", back_populates="offer", uselist=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=True)
    supplier_name = Column(String(255))
    supplier_email = Column(String(255))
    price_score = Column(Float)
    delivery_score = Column(Float)
    warranty_score = Column(Float)
    payment_score = Column(Float)
    budget_fit_score = Column(Float)
    rse_score = Column(Float)
    qualite_score = Column(Float)
    cout_score = Column(Float)
    delais_score = Column(Float)
    performance_score = Column(Float)
    overall_score = Column(Float)
    rank = Column(Integer)
    recommendation = Column(Text)
    report_path = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    request = relationship("ProcurementRequest", back_populates="evaluations")
    offer = relationship("Offer", back_populates="evaluation")


class SourcingAuditLog(Base):
    __tablename__ = "sourcing_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_email = Column(String(255))
    supplier_website = Column(Text)
    source = Column(String(50))  # 'internal_db' or 'web_search'
    action = Column(String(50), nullable=False)  # 'retained', 'excluded', 'no_email', 'duplicate'
    reason = Column(Text)
    relevance_score = Column(Float)
    search_query = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class SupplierBlacklist(Base):
    __tablename__ = "supplier_blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_name = Column(String(255), nullable=False)
    supplier_email = Column(String(255))
    reason = Column(Text, nullable=False)
    blacklisted_by = Column(String(255), default="admin")
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=True)
    agent = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'info', 'warning', 'error', 'success'
    message = Column(Text, nullable=False)
    details = Column(Text)  # JSON extra data
    created_at = Column(DateTime(timezone=True), default=utcnow)

    request = relationship("ProcurementRequest", backref="events")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id"), nullable=False)
    po_reference = Column(String(50), unique=True, nullable=False)
    supplier_name = Column(String(255), nullable=False)
    supplier_email = Column(String(255))
    product = Column(Text, nullable=False)
    quantity = Column(Float)
    unit = Column(String(50))
    unit_price = Column(Float)
    total_price = Column(Float)
    currency = Column(String(10), default="TND")
    delivery_address = Column(Text)
    cost_center = Column(String(100))
    department = Column(String(100))
    requester_name = Column(String(255))
    requester_email = Column(String(255))
    notes = Column(Text)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    delivery_status = Column(String(50), default="awaiting_delivery")
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    request = relationship("ProcurementRequest", backref="purchase_orders")
    evaluation = relationship("Evaluation", backref="purchase_order")


# ── Engine & Session ─────────────────────────────────────────────────────────

def get_engine(url: str = None):
    return create_engine(url or settings.database_url, echo=False)


def get_session_factory(engine=None):
    eng = engine or get_engine()
    return sessionmaker(bind=eng)


def create_tables(engine=None):
    eng = engine or get_engine()
    Base.metadata.create_all(eng)
