# services/production.py -- BOM, production, job work, cost roll-up
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date
from db.models import Base, Item
from db.engine import get_session
from core import stock


class BOMLine(Base):
    __tablename__ = "bom_line"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    product_item_id = Column(Integer, index=True)
    component_item_id = Column(Integer)
    qty = Column(Float, default=0.0)


class ProductionOrder(Base):
    __tablename__ = "production_order"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    product_item_id = Column(Integer, index=True)
    qty = Column(Float, default=0.0)
    pdate = Column(Date)
    status = Column(String, default="Completed")
    expected_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)


def _ensure(s):
    BOMLine.__table__.create(bind=s.get_bind(), checkfirst=True)
    ProductionOrder.__table__.create(bind=s.get_bind(), checkfirst=True)


def item_names():
    s = get_session()
    return [i.name for i in s.query(Item).order_by(Item.name).all()]


def _item(s, name):
    return s.query(Item).filter(Item.name == name).first()


def add_bom(product_name, component_name, qty):
    s = get_session()
    _ensure(s)
    p = _item(s, product_name)
    c = _item(s, component_name)
    if not p or not c:
        return {"ok": False, "msg": "Item not found"}
    s.add(BOMLine(product_item_id=p.id, component_item_id=c.id,
                  qty=float(qty or 0)))
    s.commit()
    return {"ok": True, "msg": "BOM line added"}


def bom_of(product_name):
    s = get_session()
    _ensure(s)
    p = _item(s, product_name)
    if not p:
        return []
    names = {i.id: i.name for i in s.query(Item).all()}
    return [{"component": names.get(b.component_item_id, "?"),
             "qty": b.qty}
            for b in s.query(BOMLine)
            .filter(BOMLine.product_item_id == p.id).all()]


def _avg_cost(s, item_id):
    try:
        return stock.avg_cost(s, item_id) or 0.0
    except Exception:
        return 0.0


def produce(product_name, qty, pdate=None):
    s = get_session()
    _ensure(s)
    p = _item(s, product_name)
    if not p:
        return {"ok": False, "msg": "Product not found"}
    lines = (s.query(BOMLine)
             .filter(BOMLine.product_item_id == p.id).all())
    if not lines:
        return {"ok": False, "msg": "No BOM defined for this product"}
    qty = float(qty or 0)
    pdate = pdate or date.today()
    po = ProductionOrder(product_item_id=p.id, qty=qty, pdate=pdate,
                         status="Completed")
    s.add(po)
    s.flush()
    try:
        expected = 0.0
        for b in lines:
            need = (b.qty or 0) * qty
            rate = _avg_cost(s, b.component_item_id)
            expected += need * rate
            stock.record_movement(s, b.component_item_id, 0, need,
                                  rate, None, po.id, pdate)
        unit = expected / qty if qty else 0
        stock.record_movement(s, p.id, qty, 0, unit, None, po.id, pdate)
        po.expected_cost = round(expected, 2)
        po.actual_cost = round(expected, 2)
        s.commit()
        return {"ok": True, "id": po.id, "cost": round(expected, 2),
                "unit_cost": round(unit, 2)}
    except Exception as e:
        s.rollback()
        return {"ok": False, "msg": str(e)}


def orders():
    s = get_session()
    _ensure(s)
    names = {i.id: i.name for i in s.query(Item).all()}
    out = []
    for po in (s.query(ProductionOrder)
               .order_by(ProductionOrder.id.desc()).limit(200).all()):
        out.append({"id": po.id,
                    "product": names.get(po.product_item_id, "?"),
                    "qty": po.qty, "date": str(po.pdate),
                    "cost": po.actual_cost,
                    "unit_cost": round((po.actual_cost or 0)
                                       / (po.qty or 1), 2)})
    return out