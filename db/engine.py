# db/engine.py
"""Per-company SQLite connection management.
Each company lives in its own file under the /companies folder.
New feature tables (Days 22+) live in extra model modules that are imported
automatically here, so a company database always ends up with every table.
"""
import os
import importlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

COMPANIES_DIR = os.path.join(os.getcwd(), "companies")
os.makedirs(COMPANIES_DIR, exist_ok=True)

SessionLocal = None
_engine = None

# Extra model modules added on later days. Each does `from db.models import
# Base` and defines new tables. We import whichever exist so their tables get
# created. Missing ones are skipped safely (you add them on later days).
EXTRA_MODEL_MODULES = [
    "db.models_orders",
    "db.models_inventory",
    "db.models_mfg",
    "db.models_pricing",
    "db.models_costing",
    "db.models_tax",
    "db.models_banking",
    "db.models_comm",
    "db.models_currency",
]


def _load_extra_models():
    for name in EXTRA_MODEL_MODULES:
        try:
            importlib.import_module(name)
        except ModuleNotFoundError:
            pass


def company_path(company_slug: str) -> str:
    safe = "".join(c for c in company_slug if c.isalnum() or c in " _-").strip()
    return os.path.join(COMPANIES_DIR, f"{safe}.db")


def open_company(company_slug: str):
    """Open (or create) a company DB and bind the global session factory."""
    global SessionLocal, _engine
    path = company_path(company_slug)
    _engine = create_engine(f"sqlite:///{path}", echo=False, future=True)
    _load_extra_models()               # register any later-day tables
    Base.metadata.create_all(_engine)  # creates tables if not present
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, future=True)
    return path


def get_session():
    if SessionLocal is None:
        raise RuntimeError("No company is open. Call open_company() first.")
    return SessionLocal()


def list_companies():
    return [f[:-3] for f in os.listdir(COMPANIES_DIR) if f.endswith(".db")]