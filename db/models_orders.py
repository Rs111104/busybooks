# db/models_orders.py
"""Order processing tables (Day 22): quotations, sales/purchase orders and
delivery challans. They share one Order + OrderItem structure and are
distinguished by otype (Sales/Purchase) and stage (Quotation/Order/Challan).
Imported automatically by db/engine.py.
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from db.models import Base


class Order(Base):
    __tablename__ = "order_doc"
    id = Column(Integer, primary_key=True)
    otype = Column(String, nullable=False)       # Sales / Purchase
    stage = Column(String, default="Order")       # Quotation / Order / Challan
    number = Column(String)
    date = Column(Date, default=date.today)
    party_id = Column(Integer, ForeignKey("ledger_account.id"))
    narration = Column(Text)
    total = Column(Float, default=0.0)
    status = Column(String, default="Open")       # Open / Partial / Closed
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("OrderItem", cascade="all, delete-orphan",
                         back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_item"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order_doc.id"))
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    qty = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)
    gst_rate = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    invoiced_qty = Column(Float, default=0.0)     # how much already billed
    order = relationship("Order", back_populates="items")