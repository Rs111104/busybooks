# db/models_tax.py
"""Tax tables (Day 27): TDS/TCS sections and recorded deductions/collections.
Imported automatically by db/engine.py.
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey
)
from db.models import Base


class TDSSection(Base):
    __tablename__ = "tds_section"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)   # e.g. 194C
    name = Column(String)
    rate = Column(Float, default=0.0)
    threshold = Column(Float, default=0.0)
    kind = Column(String, default="TDS")                 # TDS / TCS


class TaxDeduction(Base):
    __tablename__ = "tax_deduction"
    id = Column(Integer, primary_key=True)
    kind = Column(String, default="TDS")                 # TDS / TCS
    section_code = Column(String)
    party_id = Column(Integer, ForeignKey("ledger_account.id"))
    base_amount = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    date = Column(Date, default=date.today)
    narration = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)