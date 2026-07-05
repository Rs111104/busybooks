# db/models_mfg.py
"""Manufacturing tables (Day 24): Bill of Materials header + components.
Imported automatically by db/engine.py.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.models import Base


class BOM(Base):
    __tablename__ = "bom"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    product_item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    output_qty = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    components = relationship("BOMComponent", backref="bom",
                             cascade="all, delete-orphan")


class BOMComponent(Base):
    __tablename__ = "bom_component"
    id = Column(Integer, primary_key=True)
    bom_id = Column(Integer, ForeignKey("bom.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    qty = Column(Float, default=0.0)