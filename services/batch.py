# services/batch.py -- batch & serial number tracking
from datetime import date, datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, Date
from db.models import Base, Item
from db.engine import get_session


class Batch(Base):
    __tablename__ = "batch"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, index=True)
    batch_no = Column(String)
    mfg_date = Column(Date)
    expiry_date = Column(Date)
    qty = Column(Float, default=0.0)
    rate = Column(Float, default=0.0)


class Serial(Base):
    __tablename__ = "serial_no"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, index=True)
    serial_no = Column(String)
    status = Column(String, default="In Stock")


def _ensure(s):
    Batch.__table__.create(bind=s.get_bind(), checkfirst=True)
    Serial.__table__.create(bind=s.get_bind(), checkfirst=True)


def _d(x):
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    try:
        return datetime.strptime(str(x)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def item_names():
    s = get_session()
    return [i.name for i in s.query(Item).order_by(Item.name).all()]


def _item(s, name):
    return s.query(Item).filter(Item.name == name).first()


def add_batch(item_name, batch_no, qty, rate=0.0, mfg_date=None,
              expiry_date=None):
    s = get_session()
    _ensure(s)
    it = _item(s, item_name)
    if not it:
        return {"ok": False, "msg": "Item not found"}
    b = Batch(item_id=it.id, batch_no=batch_no, qty=float(qty or 0),
              rate=float(rate or 0), mfg_date=_d(mfg_date),
              expiry_date=_d(expiry_date))
    s.add(b)
    s.commit()
    return {"ok": True, "id": b.id, "msg": "Batch added"}


def list_batches():
    s = get_session()
    _ensure(s)
    names = {i.id: i.name for i in s.query(Item).all()}
    out = []
    for b in s.query(Batch).order_by(Batch.expiry_date).all():
        out.append({"id": b.id, "item": names.get(b.item_id, "?"),
                    "batch_no": b.batch_no, "qty": b.qty, "rate": b.rate,
                    "mfg": str(b.mfg_date or ""),
                    "expiry": str(b.expiry_date or "")})
    return out


def expiring_soon(days=30):
    s = get_session()
    _ensure(s)
    limit = date.today() + timedelta(days=int(days))
    names = {i.id: i.name for i in s.query(Item).all()}
    out = []
    for b in s.query(Batch).all():
        if b.expiry_date and b.expiry_date <= limit:
            out.append({"item": names.get(b.item_id, "?"),
                        "batch_no": b.batch_no, "qty": b.qty,
                        "expiry": str(b.expiry_date),
                        "days_left": (b.expiry_date
                                      - date.today()).days})
    out.sort(key=lambda r: r["days_left"])
    return out


def add_serials(item_name, serials):
    s = get_session()
    _ensure(s)
    it = _item(s, item_name)
    if not it:
        return {"ok": False, "msg": "Item not found"}
    n = 0
    for sn in [x.strip() for x in serials if x.strip()]:
        s.add(Serial(item_id=it.id, serial_no=sn, status="In Stock"))
        n += 1
    s.commit()
    return {"ok": True, "count": n}


def list_serials(item_name=None):
    s = get_session()
    _ensure(s)
    names = {i.id: i.name for i in s.query(Item).all()}
    q = s.query(Serial)
    if item_name:
        it = _item(s, item_name)
        if it:
            q = q.filter(Serial.item_id == it.id)
    return [{"id": x.id, "item": names.get(x.item_id, "?"),
             "serial_no": x.serial_no, "status": x.status}
            for x in q.order_by(Serial.id.desc()).limit(500).all()]