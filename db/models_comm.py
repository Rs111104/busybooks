# db/models_comm.py
"""Communication tables (Day 32): message templates and a send log.
Imported automatically by db/engine.py.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey
)
from db.models import Base


class MessageTemplate(Base):
    __tablename__ = "msg_template"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    channel = Column(String, default="Email")   # Email / SMS / WhatsApp
    subject = Column(String)
    body = Column(Text)


class MessageLog(Base):
    __tablename__ = "msg_log"
    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey("ledger_account.id"))
    channel = Column(String)
    to_addr = Column(String)
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="Saved to outbox")
    at = Column(DateTime, default=datetime.utcnow)