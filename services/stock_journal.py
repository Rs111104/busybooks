# services/stock_journal.py -- godown transfer + stock adjustment
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date
from db.models import Base, Item
from db.engine import get_session
from core import stock

try:
    from db.models import Godown
except Exception:
    Godown = None


class StockJournal(Base):
    __tablename__ = "stock_journal"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    jtype = Column(String, default="Transfer")
    item_id = Column(Integer, index=True)
    from_godown_id = Column(Integer)
    to_godown_id = Column(Integer)
    qty = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)
    jdate = Column(Date)
    narration = Column(String)


def _ensure(s):
    StockJournal.__table__.create(bind=s.get_bind(), checkfirst=True)


def item_names():
    s = get_session()
    return [i.name for i in s.query(Item).order_by(Item.name).all()]


def godown_names():
    if Godown is None:
        return []
    s = get_session()
    try:
        return [g.name for g in s.query(Godown).order_by(Godown.name).all()]
    except Exception:
        return []


def _item(s, name):
    return s.query(Item).filter(Item.name == name).first()


def _godown_id(s, name):
    if not name or Godown is None:
        return None
    try:
        g = s.query(Godown).filter(Godown.name == name).first()
        return g.id if g else None
    except Exception:
        return None


def transfer(item_name, from_godown, to_godown, qty, rate=0.0,
             jdate=None, narration=""):
    s = get_session()
    _ensure(s)
    it = _item(s, item_name)
    if not it:
        return {"ok": False, "msg": "Item not found"}
    fg = _godown_id(s, from_godown)
    tg = _godown_id(s, to_godown)
    jdate = jdate or date.today()
    j = StockJournal(jtype="Transfer", item_id=it.id, from_godown_id=fg,
                     to_godown_id=tg, qty=float(qty or 0),
                     rate=float(rate or 0), jdate=jdate,
                     narration=narration)
    s.add(j)
    s.flush()
    try:
        stock.record_movement(s, it.id, 0, float(qty or 0),
                              float(rate or 0), fg, j.id, jdate)
        stock.record_movement(s, it.id, float(qty or 0), 0,
                              float(rate or 0), tg, j.id, jdate)
        s.commit()
        return {"ok": True, "msg": "Transferred", "id": j.id}
    except Exception as e:
        s.rollback()
        return {"ok": False, "msg": str(e)}


def adjust(item_name, qty, direction="In", godown=None, rate=0.0,
           jdate=None, narration=""):
    s = get_session()
    _ensure(s)
    it = _item(s, item_name)
    if not it:
        return {"ok": False, "msg": "Item not found"}
    g = _godown_id(s, godown)
    jdate = jdate or date.today()
    j = StockJournal(jtype="Adjust-" + direction, item_id=it.id,
                     from_godown_id=g, to_godown_id=g,
                     qty=float(qty or 0), rate=float(rate or 0),
                     jdate=jdate, narration=narration)
    s.add(j)
    s.flush()
    try:
        if direction == "In":
            stock.record_movement(s, it.id, float(qty or 0), 0,
                                  float(rate or 0), g, j.id, jdate)
        else:
            stock.record_movement(s, it.id, 0, float(qty or 0),
                                  float(rate or 0), g, j.id, jdate)
        s.commit()
        return {"ok": True, "msg": "Adjusted", "id": j.id}
    except Exception as e:
        s.rollback()
        return {"ok": False, "msg": str(e)}


def journal_list(limit=300):
    s = get_session()
    _ensure(s)
    names = {i.id: i.name for i in s.query(Item).all()}
    out = []
    for j in (s.query(StockJournal)
              .order_by(StockJournal.id.desc()).limit(limit).all()):
        out.append({"id": j.id, "type": j.jtype,
                    "item": names.get(j.item_id, "?"), "qty": j.qty,
                    "rate": j.rate, "date": str(j.jdate),
                    "narration": j.narration or ""})
    return out