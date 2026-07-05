# services/fin_year.py -- multiple financial years
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date
from db.models import Base
from db.engine import get_session


class FinancialYear(Base):
    __tablename__ = "financial_year"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    active = Column(Integer, default=0)


def _ensure(s):
    FinancialYear.__table__.create(bind=s.get_bind(), checkfirst=True)


def _d(x):
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    try:
        return datetime.strptime(str(x)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def add_year(name, start, end):
    s = get_session()
    _ensure(s)
    fy = FinancialYear(name=name, start_date=_d(start),
                       end_date=_d(end), active=0)
    s.add(fy)
    s.commit()
    return {"ok": True, "id": fy.id}


def list_years():
    s = get_session()
    _ensure(s)
    return [{"id": y.id, "name": y.name,
             "start": str(y.start_date or ""),
             "end": str(y.end_date or ""),
             "active": bool(y.active)}
            for y in s.query(FinancialYear)
            .order_by(FinancialYear.start_date).all()]


def set_active(year_id):
    s = get_session()
    _ensure(s)
    for y in s.query(FinancialYear).all():
        y.active = 1 if y.id == year_id else 0
    s.commit()
    return True


def active_year():
    s = get_session()
    _ensure(s)
    y = (s.query(FinancialYear)
         .filter(FinancialYear.active == 1).first())
    if not y:
        return None
    return {"id": y.id, "name": y.name,
            "start": str(y.start_date or ""),
            "end": str(y.end_date or "")}