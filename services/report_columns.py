# services/report_columns.py -- user-definable report columns
import json
from sqlalchemy import Column, Integer, String, Text
from db.models import Base
from db.engine import get_session

_COLUMNS = {
    "Ledgers": ["name", "group", "balance", "gstin", "state"],
    "Items": ["name", "hsn", "gst_rate", "sale_rate",
              "purchase_rate"],
    "Stock": ["item", "qty", "rate", "value"],
}


class ColumnPreset(Base):
    __tablename__ = "column_preset"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    report = Column(String)
    columns_json = Column(Text)


def _ensure(s):
    ColumnPreset.__table__.create(bind=s.get_bind(), checkfirst=True)


def reports():
    return list(_COLUMNS.keys())


def available_columns(report):
    return list(_COLUMNS.get(report, []))


def project(rows, columns):
    return [{c: r.get(c) for c in columns} for r in (rows or [])]


def fetch_rows(report):
    s = get_session()
    from db.models import Ledger, Item
    if report == "Ledgers":
        out = []
        for l in s.query(Ledger).order_by(Ledger.name).all():
            out.append({"name": l.name,
                        "group": getattr(l, "group_id", ""),
                        "balance": getattr(l, "opening_balance", 0)
                        or 0,
                        "gstin": getattr(l, "gstin", "") or "",
                        "state": getattr(l, "state", "") or ""})
        return out
    if report == "Items":
        out = []
        for i in s.query(Item).order_by(Item.name).all():
            out.append({"name": i.name,
                        "hsn": getattr(i, "hsn", "") or "",
                        "gst_rate": getattr(i, "gst_rate", 0) or 0,
                        "sale_rate": getattr(i, "sale_rate", 0) or 0,
                        "purchase_rate": getattr(i, "purchase_rate",
                                                 0) or 0})
        return out
    if report == "Stock":
        try:
            from core import stock
            return [{"item": r.get("name"), "qty": r.get("qty"),
                     "rate": r.get("rate"), "value": r.get("value")}
                    for r in stock.summary(s)]
        except Exception:
            return []
    return []


def save_preset(name, report, columns):
    s = get_session()
    _ensure(s)
    p = ColumnPreset(name=name, report=report,
                     columns_json=json.dumps(columns))
    s.add(p)
    s.commit()
    return {"ok": True, "id": p.id}


def list_presets(report=None):
    s = get_session()
    _ensure(s)
    q = s.query(ColumnPreset)
    if report:
        q = q.filter(ColumnPreset.report == report)
    out = []
    for p in q.order_by(ColumnPreset.id.desc()).all():
        try:
            cols = json.loads(p.columns_json or "[]")
        except Exception:
            cols = []
        out.append({"id": p.id, "name": p.name, "report": p.report,
                    "columns": cols})
    return out