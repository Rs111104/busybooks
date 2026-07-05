# db/models_banking.py
"""Banking tables (Day 30): imported bank statement lines for reconciliation.
Imported automatically by db/engine.py.
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey
)
from db.models import Base


class BankStatementLine(Base):
    __tablename__ = "bank_stmt_line"
    id = Column(Integer, primary_key=True)
    bank_ledger_id = Column(Integer, ForeignKey("ledger_account.id"))
    date = Column(Date, default=date.today)
    description = Column(String)
    ref = Column(String)
    amount = Column(Float, default=0.0)
    dc = Column(String, default="Dr")          # Dr = money in, Cr = money out
    reconciled = Column(Integer, default=0)     # 0 / 1
    matched_voucher_id = Column(Integer, ForeignKey("voucher.id"))
    created_at = Column(DateTime, default=datetime.utcnow)