# services/payroll.py -- employees + payslips (PF/ESI)
from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date
from db.models import Base
from db.engine import get_session


class Employee(Base):
    __tablename__ = "employee"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String)
    basic = Column(Float, default=0.0)
    hra = Column(Float, default=0.0)
    allowances = Column(Float, default=0.0)
    pf_pct = Column(Float, default=12.0)
    esi_pct = Column(Float, default=0.75)
    active = Column(Integer, default=1)
    doj = Column(Date)


class Payslip(Base):
    __tablename__ = "payslip"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, index=True)
    period = Column(String)
    gross = Column(Float)
    pf = Column(Float)
    esi = Column(Float)
    other_ded = Column(Float, default=0.0)
    net = Column(Float)
    created_at = Column(Date)


def _ensure(s):
    Employee.__table__.create(bind=s.get_bind(), checkfirst=True)
    Payslip.__table__.create(bind=s.get_bind(), checkfirst=True)


def add_employee(name, basic=0.0, hra=0.0, allowances=0.0,
                 pf_pct=12.0, esi_pct=0.75, code=""):
    s = get_session()
    _ensure(s)
    e = Employee(name=name, basic=float(basic or 0), hra=float(hra or 0),
                 allowances=float(allowances or 0), pf_pct=float(pf_pct),
                 esi_pct=float(esi_pct), code=code, active=1,
                 doj=date.today())
    s.add(e)
    s.commit()
    return e.id


def list_employees(active_only=True):
    s = get_session()
    _ensure(s)
    q = s.query(Employee)
    if active_only:
        q = q.filter(Employee.active == 1)
    return [{"id": e.id, "name": e.name, "code": e.code, "basic": e.basic,
             "hra": e.hra, "allowances": e.allowances,
             "pf_pct": e.pf_pct, "esi_pct": e.esi_pct}
            for e in q.order_by(Employee.name).all()]


def _calc(e, other_ded=0.0):
    gross = (e.basic or 0) + (e.hra or 0) + (e.allowances or 0)
    pf = round((e.basic or 0) * (e.pf_pct or 0) / 100.0, 2)
    esi = round(gross * (e.esi_pct or 0) / 100.0, 2)
    net = round(gross - pf - esi - (other_ded or 0), 2)
    return round(gross, 2), pf, esi, net


def generate_payslip(employee_id, period, other_ded=0.0):
    s = get_session()
    _ensure(s)
    e = s.get(Employee, employee_id)
    if not e:
        return None
    gross, pf, esi, net = _calc(e, other_ded)
    p = Payslip(employee_id=e.id, period=period, gross=gross, pf=pf,
                esi=esi, other_ded=float(other_ded or 0), net=net,
                created_at=date.today())
    s.add(p)
    s.commit()
    return p.id


def run_payroll(period):
    s = get_session()
    _ensure(s)
    done = []
    for e in s.query(Employee).filter(Employee.active == 1).all():
        exists = (s.query(Payslip)
                  .filter(Payslip.employee_id == e.id,
                          Payslip.period == period).first())
        if exists:
            continue
        done.append(generate_payslip(e.id, period))
    return done


def payslips(period=None):
    s = get_session()
    _ensure(s)
    q = s.query(Payslip)
    if period:
        q = q.filter(Payslip.period == period)
    names = {e.id: e.name for e in s.query(Employee).all()}
    return [{"id": p.id, "employee": names.get(p.employee_id, "?"),
             "period": p.period, "gross": p.gross, "pf": p.pf,
             "esi": p.esi, "other_ded": p.other_ded, "net": p.net}
            for p in q.order_by(Payslip.period).all()]