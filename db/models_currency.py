# db/models_currency.py
"""Multi-currency table (Day 34). Imported automatically by db/engine.py."""
from sqlalchemy import Column, Integer, String, Float
from db.models import Base


class Currency(Base):
    __tablename__ = "currency"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)   # e.g. USD
    name = Column(String)
    symbol = Column(String, default="")
    rate_to_base = Column(Float, default=1.0)   # 1 unit = X base currency