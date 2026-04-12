"""
agents/agent_storage/tools.py
Database operations for the Storage Agent.
No LLM needed — pure CRUD with SQLAlchemy.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from db.models import (
    ProcurementRequest, Supplier, RFQ, Offer, Evaluation,
    get_engine, get_session_factory, create_tables,
)
from logger import get_logger

logger = get_logger(__name__)


class StorageTools:
    """Database CRUD operations for the procurement pipeline."""

    def __init__(self, database_url: str = None):
        self._engine = get_engine(database_url)
        self._Session = get_session_factory(self._engine)
        create_tables(self._engine)

    def _session(self):
        return self._Session()

    # ── Procurement Request ──────────────────────────────────────────────────

    def store_request(self, spec: dict) -> str:
        """
        Store a ProcurementSpec from Agent 1.
        Returns the request_id (UUID string).
        """
        session = self._session()
        try:
            req = ProcurementRequest(
                product=spec.get("product", ""),
                category=spec.get("category", ""),
                quantity=spec.get("quantity"),
                unit=spec.get("unit"),
                budget_min=spec.get("budget_min"),
                budget_max=spec.get("budget_max"),
                deadline=spec.get("deadline"),
                requester_email=spec.get("requester_email", ""),
                is_valid=spec.get("is_valid", True),
                rejection_reason=spec.get("rejection_reason"),
                status="pending",
            )
            session.add(req)
            session.commit()
            request_id = str(req.id)
            logger.info("Stored procurement request", extra={"request_id": request_id})
            return request_id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to store request", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    # ── Suppliers ────────────────────────────────────────────────────────────

    def store_suppliers(self, request_id: str, supplier_list: dict) -> list:
        """
        Store suppliers from Agent 2.
        Returns list of (supplier_name, supplier_db_id) tuples.
        """
        session = self._session()
        try:
            req_uuid = uuid.UUID(request_id)
            result = []
            for s in supplier_list.get("suppliers", []):
                supplier = Supplier(
                    request_id=req_uuid,
                    name=s.get("name", ""),
                    website=s.get("website"),
                    email=s.get("email"),
                    country=s.get("country"),
                    category=s.get("category"),
                    relevance_score=s.get("relevance_score"),
                    source_url=s.get("source_url"),
                )
                session.add(supplier)
                session.flush()
                result.append((s.get("name", ""), str(supplier.id)))

            session.commit()
            logger.info("Stored suppliers", extra={
                "request_id": request_id, "count": len(result),
            })
            return result
        except Exception as exc:
            session.rollback()
            logger.error("Failed to store suppliers", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    # ── RFQs ─────────────────────────────────────────────────────────────────

    def store_rfqs(self, request_id: str, rfq_records: list, supplier_map: dict) -> list:
        """
        Store RFQ records from Agent 3 Phase 1.

        Args:
            request_id: UUID string
            rfq_records: list of RFQRecord dicts
            supplier_map: dict mapping supplier_email -> supplier_db_id

        Returns:
            list of (supplier_name, rfq_db_id) tuples.
        """
        session = self._session()
        try:
            req_uuid = uuid.UUID(request_id)
            result = []
            for r in rfq_records:
                email = r.get("supplier_email", "")
                supplier_id = supplier_map.get(email)
                if not supplier_id:
                    logger.warning("No supplier_id for email", extra={"email": email})
                    continue

                rfq = RFQ(
                    request_id=req_uuid,
                    supplier_id=uuid.UUID(supplier_id),
                    subject=r.get("subject", ""),
                    message_id=r.get("message_id"),
                    status=r.get("status", "failed"),
                    sent_at=datetime.fromisoformat(r["sent_at"]) if r.get("sent_at") else None,
                )
                session.add(rfq)
                session.flush()
                result.append((r.get("supplier_name", ""), str(rfq.id)))

            session.commit()
            logger.info("Stored RFQs", extra={
                "request_id": request_id, "count": len(result),
            })
            return result
        except Exception as exc:
            session.rollback()
            logger.error("Failed to store RFQs", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    # ── Offers ───────────────────────────────────────────────────────────────

    def store_offers(self, request_id: str, offers: list, supplier_map: dict, rfq_map: dict) -> list:
        """
        Store parsed supplier offers from Agent 3 Phase 2.

        Args:
            request_id: UUID string
            offers: list of SupplierOffer dicts
            supplier_map: dict mapping supplier_email -> supplier_db_id
            rfq_map: dict mapping supplier_email -> rfq_db_id

        Returns:
            list of (supplier_name, offer_db_id) tuples.
        """
        session = self._session()
        try:
            req_uuid = uuid.UUID(request_id)
            # Fallback: first known supplier/rfq pair (used when test email ≠ real supplier)
            fallback_supplier_id = next(iter(supplier_map.values()), None) if supplier_map else None
            fallback_rfq_id = next(iter(rfq_map.values()), None) if rfq_map else None
            result = []
            for o in offers:
                email = o.get("supplier_email", "")
                supplier_id = supplier_map.get(email) or fallback_supplier_id
                rfq_id = rfq_map.get(email) or fallback_rfq_id
                if not supplier_id or not rfq_id:
                    logger.warning("Missing supplier/rfq mapping for offer", extra={"email": email})
                    continue
                if email not in supplier_map:
                    logger.info("Offer email not in supplier map — assigned to fallback supplier",
                                extra={"email": email})

                offer = Offer(
                    request_id=req_uuid,
                    supplier_id=uuid.UUID(supplier_id),
                    rfq_id=uuid.UUID(rfq_id),
                    unit_price=o.get("unit_price"),
                    total_price=o.get("total_price"),
                    currency=o.get("currency", "TND"),
                    delivery_days=o.get("delivery_days"),
                    warranty=o.get("warranty"),
                    payment_terms=o.get("payment_terms"),
                    notes=o.get("notes"),
                    raw_body=o.get("raw_body"),
                    has_pdf=o.get("has_pdf", False),
                )
                session.add(offer)
                session.flush()
                result.append((o.get("supplier_name", ""), str(offer.id)))

            session.commit()
            logger.info("Stored offers", extra={
                "request_id": request_id, "count": len(result),
            })
            return result
        except Exception as exc:
            session.rollback()
            logger.error("Failed to store offers", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    # ── Evaluations ────────────────────────────────────────────────────────

    def store_evaluations(self, request_id: str, evaluation_scores: list, report_path: str = None) -> list:
        """
        Store QCDP evaluation scores from Agent 5.
        Returns list of (supplier_name, evaluation_db_id) tuples.
        """
        session = self._session()
        try:
            req_uuid = uuid.UUID(request_id)
            # Build a lookup: supplier_email -> offer_id
            offers = session.query(Offer).filter_by(request_id=req_uuid).all()
            email_to_offer = {}
            for o in offers:
                sup = session.query(Supplier).filter_by(id=o.supplier_id).first()
                if sup and sup.email:
                    email_to_offer[sup.email.lower()] = o.id
                if sup and sup.name:
                    email_to_offer[sup.name.lower()] = o.id
            # Fallback: use the first offer if only one exists
            fallback_offer_id = offers[0].id if len(offers) == 1 else None

            result = []
            for s in evaluation_scores:
                supplier_email = s.get("supplier_email", "").lower()
                supplier_name = s.get("supplier_name", "").lower()
                offer_id = (
                    s.get("offer_id")
                    or email_to_offer.get(supplier_email)
                    or email_to_offer.get(supplier_name)
                    or fallback_offer_id
                )
                if not offer_id:
                    logger.warning("No offer_id found for evaluation",
                                   extra={"supplier": s.get("supplier_name"), "email": supplier_email})
                    continue

                eval_record = Evaluation(
                    request_id=req_uuid,
                    offer_id=offer_id,
                    supplier_name=s.get("supplier_name", ""),
                    supplier_email=s.get("supplier_email", ""),
                    price_score=s.get("price_score"),
                    delivery_score=s.get("delivery_score"),
                    warranty_score=s.get("warranty_score"),
                    payment_score=s.get("payment_score"),
                    budget_fit_score=s.get("budget_fit_score"),
                    rse_score=s.get("rse_score"),
                    qualite_score=s.get("qualite_score"),
                    cout_score=s.get("cout_score"),
                    delais_score=s.get("delais_score"),
                    performance_score=s.get("performance_score"),
                    overall_score=s.get("overall_score"),
                    rank=s.get("rank"),
                    recommendation=s.get("recommendation"),
                    report_path=report_path,
                )
                session.add(eval_record)
                session.flush()
                result.append((s.get("supplier_name", ""), str(eval_record.id)))

            session.commit()
            logger.info("Stored evaluations", extra={
                "request_id": request_id, "count": len(result),
            })
            return result
        except Exception as exc:
            session.rollback()
            logger.error("Failed to store evaluations", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    # ── Queries ──────────────────────────────────────────────────────────────

    def get_request(self, request_id: str) -> Optional[dict]:
        """Fetch a procurement request by ID."""
        session = self._session()
        try:
            req = session.query(ProcurementRequest).filter_by(
                id=uuid.UUID(request_id)
            ).first()
            if not req:
                return None
            return {
                "id": str(req.id),
                "product": req.product,
                "category": req.category,
                "quantity": req.quantity,
                "unit": req.unit,
                "budget_min": req.budget_min,
                "budget_max": req.budget_max,
                "deadline": req.deadline,
                "requester_email": req.requester_email,
                "is_valid": req.is_valid,
                "status": req.status,
                "created_at": req.created_at.isoformat() if req.created_at else None,
            }
        finally:
            session.close()

    def get_offers_for_request(self, request_id: str) -> list:
        """Fetch all offers for a procurement request."""
        session = self._session()
        try:
            offers = session.query(Offer).filter_by(
                request_id=uuid.UUID(request_id)
            ).all()
            return [
                {
                    "id": str(o.id),
                    "supplier_id": str(o.supplier_id),
                    "unit_price": o.unit_price,
                    "total_price": o.total_price,
                    "currency": o.currency,
                    "delivery_days": o.delivery_days,
                    "warranty": o.warranty,
                    "payment_terms": o.payment_terms,
                    "notes": o.notes,
                    "has_pdf": o.has_pdf,
                    "received_at": o.received_at.isoformat() if o.received_at else None,
                }
                for o in offers
            ]
        finally:
            session.close()

    def get_pending_requests(self) -> list:
        """
        Fetch all procurement requests with status='awaiting_responses'.
        Returns list of dicts including the rfqs for each request.
        """
        session = self._session()
        try:
            requests = session.query(ProcurementRequest).filter_by(
                status="awaiting_responses"
            ).all()
            result = []
            for req in requests:
                rfqs = session.query(RFQ).filter_by(
                    request_id=req.id
                ).all()
                result.append({
                    "id": str(req.id),
                    "product": req.product,
                    "category": req.category,
                    "quantity": req.quantity,
                    "unit": req.unit,
                    "budget_min": req.budget_min,
                    "budget_max": req.budget_max,
                    "deadline": req.deadline,
                    "requester_email": req.requester_email,
                    "status": req.status,
                    "created_at": req.created_at.isoformat() if req.created_at else None,
                    "rfqs": [
                        {
                            "id": str(r.id),
                            "supplier_id": str(r.supplier_id),
                            "subject": r.subject,
                            "status": r.status,
                            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                            "reminder_sent": r.reminder_sent,
                        }
                        for r in rfqs
                    ],
                })
            return result
        finally:
            session.close()

    def get_suppliers_for_request(self, request_id: str) -> list:
        """Fetch all suppliers for a request."""
        session = self._session()
        try:
            suppliers = session.query(Supplier).filter_by(
                request_id=uuid.UUID(request_id)
            ).all()
            return [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "email": s.email,
                    "website": s.website,
                }
                for s in suppliers
            ]
        finally:
            session.close()

    def update_request_status(self, request_id: str, status: str):
        """Update the status of a procurement request."""
        session = self._session()
        try:
            session.query(ProcurementRequest).filter_by(
                id=uuid.UUID(request_id)
            ).update({"status": status})
            session.commit()
            logger.info("Updated request status", extra={
                "request_id": request_id, "status": status,
            })
        except Exception as exc:
            session.rollback()
            logger.error("Failed to update status", extra={"error": str(exc)})
            raise
        finally:
            session.close()

    def mark_reminder_sent(self, rfq_id: str):
        """Mark an RFQ as having had a reminder sent."""
        session = self._session()
        try:
            session.query(RFQ).filter_by(
                id=uuid.UUID(rfq_id)
            ).update({
                "reminder_sent": True,
                "reminder_at": datetime.now(timezone.utc),
            })
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Failed to mark reminder", extra={"error": str(exc)})
            raise
        finally:
            session.close()
