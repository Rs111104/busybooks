# services/salesman.py -- salesman / broker-wise tracking & reporting
from sqlalchemy import Column, Integer, String
from db.models import Base, Voucher
from db.engine import get_session


class Salesman(Base):
    __tablename__ = "salesman"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class VoucherSalesman(Base):
    __tablename__ = "voucher_salesman"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    voucher_id = Column(Integer, index=True)
    salesman_id = Column(Integer)


def _ensure(s):
    bind = s.get_bind()
    Salesman.__table__.create(bind=bind, checkfirst=True)
    VoucherSalesman.__table__.create(bind=bind, checkfirst=True)


def add_salesman(name):
    s = get_session()
    _ensure(s)
    existing = s.query(Salesman).filter(Salesman.name == name).first()
    if existing:
        return existing.id
    row = Salesman(name=name)
    s.add(row)
    s.commit()
    return row.id


def list_salesmen():
    s = get_session()
    _ensure(s)
    return [{"id": r.id, "name": r.name}
            for r in s.query(Salesman).order_by(Salesman.name).all()]


def assign(voucher_id, salesman_id):
    s = get_session()
    _ensure(s)
    link = s.query(VoucherSalesman).filter(
        VoucherSalesman.voucher_id == voucher_id).first()
    if link:
        link.salesman_id = salesman_id
    else:
        s.add(VoucherSalesman(voucher_id=voucher_id,
                              salesman_id=salesman_id))
    s.commit()
    return True


def recent_sales(limit=100):
    s = get_session()
    _ensure(s)
    name_by_id = {r.id: r.name for r in s.query(Salesman).all()}
    link_by_v = {l.voucher_id: l.salesman_id
                 for l in s.query(VoucherSalesman).all()}
    out = []
    q = (s.query(Voucher).filter(Voucher.vtype == "Sales")
         .order_by(Voucher.id.desc()).limit(limit).all())
    for v in q:
        sid = link_by_v.get(v.id)
        out.append({
            "voucher_id": v.id,
            "number": v.number,
            "total": v.total or 0,
            "salesman": name_by_id.get(sid, "(unassigned)"),
        })
    return out


def sales_by_salesman():
    s = get_session()
    _ensure(s)
    name_by_id = {r.id: r.name for r in s.query(Salesman).all()}
    link_by_v = {l.voucher_id: l.salesman_id
                 for l in s.query(VoucherSalesman).all()}
    totals = {}
    for v in s.query(Voucher).filter(Voucher.vtype == "Sales").all():
        sid = link_by_v.get(v.id)
        nm = name_by_id.get(sid, "(unassigned)")
        totals[nm] = totals.get(nm, 0) + (v.total or 0)
    return [{"salesman": k, "total": round(val, 2)}
            for k, val in sorted(totals.items(), key=lambda kv: -kv[1])]