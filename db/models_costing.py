# db/models_costing.py
"""Cost accounting tables (Day 28): cost centres, allocations and budgets.
Already listed in db/engine.py's auto-loader.
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey
)
from db.models import Base


class CostCentre(Base):
    __tablename__ = "cost_centre"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("cost_centre.id"))


class CostAllocation(Base):
    __tablename__ = "cost_allocation"
    id = Column(Integer, primary_key=True)
    cost_centre_id = Column(Integer, ForeignKey("cost_centre.id"),
                            nullable=False)
    ledger_id = Column(Integer, ForeignKey("ledger_account.id"))
    voucher_id = Column(Integer, ForeignKey("voucher.id"))
    amount = Column(Float, default=0.0)
    date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budget"
    id = Column(Integer, primary_key=True)
    ledger_id = Column(Integer, ForeignKey("ledger_account.id"),
                       nullable=False)
    period = Column(String)          # YYYY-MM
    amount = Column(Float, default=0.0)