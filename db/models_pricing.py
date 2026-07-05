# db/models_pricing.py
"""Pricing tables (Day 25): price lists and their tiered per-item rates.
Imported automatically by db/engine.py.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.models import Base


class PriceList(Base):
    __tablename__ = "price_list"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    items = relationship("PriceListItem", backref="price_list",
                        cascade="all, delete-orphan")


class PriceListItem(Base):
    __tablename__ = "price_list_item"
    id = Column(Integer, primary_key=True)
    price_list_id = Column(Integer, ForeignKey("price_list.id"),
                           nullable=False)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    min_qty = Column(Float, default=1.0)   # tier starts at this quantity
    rate = Column(Float, default=0.0)# --- compatibility re-exports (keep `from db.models import X` working) ---
try:
    from db.models_pricing import PriceList  # noqa: F401
except Exception:
    pass