# services/documents.py -- Indent / Quotation / Order / Challan chain
import json
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, Text
from db.models import Base, Ledger
from db.engine import get_session

STAGES = ["Indent", "Quotation", "Order", "Challan"]


class SalesDoc(Base):
    __tablename__ = "sales_document"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    dtype = Column(String, default="Quotation")
    number = Column(String)
    party = Column(String)
    ddate = Column(Date)
    status = Column(String, default="Open")
    amount = Column(Float, default=0.0)
    lines_json = Column(Text)
    narration = Column(String)


def _ensure(s):
    SalesDoc.__table__.create(bind=s.get_bind(), checkfirst=True)


def party_names():
    s = get_session()
    alll = [l.name for l in s.query(Ledger).order_by(Ledger.name).all()]
    parties = [l.name for l in s.query(Ledger).order_by(Ledger.name).all()
               if getattr(l, "is_party", False)]
    return parties or alll


def _next_number(s, dtype):
    prefix = {"Indent": "IND", "Quotation": "QTN", "Order": "ORD",
              "Challan": "CHL"}.get(dtype, "DOC")
    n = s.query(SalesDoc).filter(SalesDoc.dtype == dtype).count() + 1
    return "%s/%04d" % (prefix, n)


def create_document(dtype, party, lines, ddate=None, narration=""):
    """lines: list of dicts {item, qty, rate}."""
    s = get_session()
    _ensure(s)
    amount = 0.0
    for ln in (lines or []):
        amount += float(ln.get("qty") or 0) * float(ln.get("rate") or 0)
    d = SalesDoc(dtype=dtype, number=_next_number(s, dtype), party=party,
                 ddate=ddate or date.today(), status="Open",
                 amount=round(amount, 2),
                 lines_json=json.dumps(lines or []), narration=narration)
    s.add(d)
    s.commit()
    return {"ok": True, "id": d.id, "number": d.number}


def list_documents(dtype=None):
    s = get_session()
    _ensure(s)
    q = s.query(SalesDoc)
    if dtype:
        q = q.filter(SalesDoc.dtype == dtype)
    out = []
    for d in q.order_by(SalesDoc.id.desc()).limit(300).all():
        out.append({"id": d.id, "dtype": d.dtype, "number": d.number,
                    "party": d.party, "date": str(d.ddate),
                    "amount": d.amount, "status": d.status})
    return out


def convert(doc_id):
    """Advance a document to the next stage."""
    s = get_session()
    _ensure(s)
    d = s.get(SalesDoc, doc_id)
    if not d:
        return {"ok": False, "msg": "Document not found"}
    try:
        idx = STAGES.index(d.dtype)
    except ValueError:
        return {"ok": False, "msg": "Unknown stage"}
    if idx >= len(STAGES) - 1:
        return {"ok": False,
                "msg": "Already at Challan. Raise the invoice from "
                       "the Sales screen."}
    nxt = STAGES[idx + 1]
    new = SalesDoc(dtype=nxt, number=_next_number(s, nxt), party=d.party,
                   ddate=date.today(), status="Open", amount=d.amount,
                   lines_json=d.lines_json, narration=d.narration)
    s.add(new)
    d.status = "Converted to " + nxt
    s.commit()
    return {"ok": True, "id": new.id, "number": new.number,
            "stage": nxt}