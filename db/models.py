# db/models.py
"""SQLAlchemy models = the full database schema for BusyBooks.
Each company is stored in its own SQLite file, so these tables live
inside every company database.
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ---------------------------------------------------------------------------
# COMPANY & SYSTEM
# ---------------------------------------------------------------------------
class Company(Base):
    """Single-row table describing the company this database belongs to."""
    __tablename__ = "company"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(Text)
    state = Column(String)             # used for GST intra/inter-state logic
    state_code = Column(String)        # 2-digit GST state code
    gstin = Column(String)
    fy_start = Column(Date, default=lambda: date(date.today().year, 4, 1))
    fy_end = Column(Date, default=lambda: date(date.today().year + 1, 3, 31))
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="operator")   # admin / operator
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)            # CREATE / UPDATE / DELETE
    entity = Column(String)            # table name
    entity_id = Column(Integer)
    detail = Column(Text)
    at = Column(DateTime, default=datetime.utcnow)


class NumberSeries(Base):
    """Voucher numbering per voucher type (e.g. Sales -> INV/0001)."""
    __tablename__ = "number_series"
    id = Column(Integer, primary_key=True)
    vtype = Column(String, unique=True, nullable=False)
    prefix = Column(String, default="")
    next_no = Column(Integer, default=1)
    width = Column(Integer, default=4)   # zero-padding width


# ---------------------------------------------------------------------------
# MASTERS
# ---------------------------------------------------------------------------
class AccountGroup(Base):
    __tablename__ = "account_group"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("account_group.id"))
    # nature drives P&L vs Balance Sheet: Asset/Liability/Income/Expense/Capital
    nature = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)
    children = relationship("AccountGroup")


class Ledger(Base):
    """Every account, including parties (customers/suppliers)."""
    __tablename__ = "ledger_account"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    group_id = Column(Integer, ForeignKey("account_group.id"), nullable=False)
    opening_balance = Column(Float, default=0.0)
    opening_dc = Column(String, default="Dr")      # Dr / Cr
    # party fields (used when this ledger is a customer/supplier)
    is_party = Column(Boolean, default=False)
    gstin = Column(String)
    address = Column(Text)
    state = Column(String)
    state_code = Column(String)
    phone = Column(String)
    email = Column(String)
    credit_limit = Column(Float, default=0.0)
    group = relationship("AccountGroup")


class Unit(Base):
    __tablename__ = "unit"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)   # e.g. Nos, Kg, Ltr
    decimals = Column(Integer, default=2)


class ItemGroup(Base):
    __tablename__ = "item_group"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("item_group.id"))


class Godown(Base):
    __tablename__ = "godown"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    address = Column(Text)


class TaxRate(Base):
    __tablename__ = "tax_rate"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)   # e.g. GST 18%
    rate = Column(Float, default=0.0)                    # total %


class Item(Base):
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    group_id = Column(Integer, ForeignKey("item_group.id"))
    unit_id = Column(Integer, ForeignKey("unit.id"))
    hsn = Column(String)
    gst_rate = Column(Float, default=0.0)
    sale_rate = Column(Float, default=0.0)
    purchase_rate = Column(Float, default=0.0)
    opening_qty = Column(Float, default=0.0)
    opening_rate = Column(Float, default=0.0)


# ---------------------------------------------------------------------------
# TRANSACTIONS (VOUCHERS)
# ---------------------------------------------------------------------------
class Voucher(Base):
    __tablename__ = "voucher"
    id = Column(Integer, primary_key=True)
    # Sales/Purchase/Payment/Receipt/Contra/Journal/CreditNote/DebitNote/StockJournal
    vtype = Column(String, nullable=False)
    number = Column(String)
    date = Column(Date, default=date.today)
    party_id = Column(Integer, ForeignKey("ledger_account.id"))
    narration = Column(Text)
    total = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    entries = relationship("VoucherEntry", cascade="all, delete-orphan",
                           back_populates="voucher")
    items = relationship("VoucherItem", cascade="all, delete-orphan",
                         back_populates="voucher")
    party = relationship("Ledger")


class VoucherEntry(Base):
    """The double-entry ledger postings. debit total MUST equal credit total."""
    __tablename__ = "voucher_entry"
    id = Column(Integer, primary_key=True)
    voucher_id = Column(Integer, ForeignKey("voucher.id"))
    ledger_id = Column(Integer, ForeignKey("ledger_account.id"), nullable=False)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    voucher = relationship("Voucher", back_populates="entries")
    ledger = relationship("Ledger")


class VoucherItem(Base):
    """Inventory lines for sales/purchase/stock vouchers."""
    __tablename__ = "voucher_item"
    id = Column(Integer, primary_key=True)
    voucher_id = Column(Integer, ForeignKey("voucher.id"))
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    godown_id = Column(Integer, ForeignKey("godown.id"))
    qty = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    gst_rate = Column(Float, default=0.0)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    voucher = relationship("Voucher", back_populates="items")
    item = relationship("Item")


class StockLedger(Base):
    """Every inventory movement, for stock summary & valuation."""
    __tablename__ = "stock_ledger"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    godown_id = Column(Integer, ForeignKey("godown.id"))
    voucher_id = Column(Integer, ForeignKey("voucher.id"))
    date = Column(Date, default=date.today)
    qty_in = Column(Float, default=0.0)
    qty_out = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)
    value = Column(Float, default=0.0)