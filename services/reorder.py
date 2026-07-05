# services/reorder.py -- reorder levels + low-stock alerts
from sqlalchemy import Column, Integer, Float
from db.models import Base, Item
from db.engine import get_session
from core import stock


class ReorderLevel(Base):
    __tablename__ = "reorder_level"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, index=True)
    level = Column(Float, default=0.0)


def _ensure(s):
    ReorderLevel.__table__.create(bind=s.get_bind(), checkfirst=True)


def item_names():
    s = get_session()
    return [i.name for i in s.query(Item).order_by(Item.name).all()]


def set_level(item_name, level):
    s = get_session()
    _ensure(s)
    it = s.query(Item).filter(Item.name == item_name).first()
    if not it:
        return False
    row = (s.query(ReorderLevel)
           .filter(ReorderLevel.item_id == it.id).first())
    if not row:
        row = ReorderLevel(item_id=it.id, level=float(level))
        s.add(row)
    else:
        row.level = float(level)
    s.commit()
    return True


def alerts():
    s = get_session()
    _ensure(s)
    levels = {r.item_id: r.level for r in s.query(ReorderLevel).all()}
    out = []
    for it in s.query(Item).all():
        lvl = levels.get(it.id, 0)
        if not lvl:
            continue
        qty = stock.current_qty(s, it.id)
        if qty <= lvl:
            out.append({"item": it.name, "qty": round(qty, 2),
                        "level": round(lvl, 2),
                        "short": round(lvl - qty, 2)})
    out.sort(key=lambda r: r["short"], reverse=True)
    return out