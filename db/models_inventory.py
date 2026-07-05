# db/models_inventory.py
"""Advanced inventory tables (Day 23): batches (with expiry) and serial
numbers. Imported automatically by db/engine.py.
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey
)
from db.models import Base


class Batch(Base):
    __tablename__ = "batch"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    batch_no = Column(String, nullable=False)
    mfg_date = Column(Date)
    expiry_date = Column(Date)
    qty = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)
    godown_id = Column(Integer, ForeignKey("godown.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Serial(Base):
    __tablename__ = "serial_no"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    serial_no = Column(String, nullable=False)
    status = Column(String, default="In Stock")   # In Stock / Sold
    voucher_id = Column(Integer, ForeignKey("voucher.id"))
    created_at = Column(DateTime, default=datetime.utcnow)