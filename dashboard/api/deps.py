"""
dashboard/api/deps.py — Shared dependencies for API routes.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.models import get_engine, get_session_factory, create_tables

_engine = get_engine()
create_tables(_engine)
_SessionFactory = get_session_factory(_engine)


def get_db():
    """Yield a DB session, auto-close after request."""
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()
