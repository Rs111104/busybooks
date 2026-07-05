# services/cheques.py -- cheque register, PDC, cheque printing
import os
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date
from db.models import Base
from db.engine import get_session


class Cheque(Base):
    __tablename__ = "cheque_register"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    party = Column(String)
    bank = Column(String)
    cheque_no = Column(String)
    amount = Column(Float, default=0.0)
    cheque_date = Column(Date)
    direction = Column(String, default="Incoming")
    status = Column(String, default="Pending")
    narration = Column(String)


def _ensure(s):
    Cheque.__table__.create(bind=s.get_bind(), checkfirst=True)


def _d(x):
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    try:
        return datetime.strptime(str(x)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def add_cheque(party, amount, cheque_no="", bank="", cheque_date=None,
               direction="Incoming", narration=""):
    s = get_session()
    _ensure(s)
    c = Cheque(party=party, amount=float(amount or 0),
               cheque_no=cheque_no, bank=bank,
               cheque_date=_d(cheque_date) or date.today(),
               direction=direction, status="Pending",
               narration=narration)
    s.add(c)
    s.commit()
    return c.id


def set_status(cheque_id, status):
    s = get_session()
    _ensure(s)
    c = s.get(Cheque, cheque_id)
    if not c:
        return False
    c.status = status
    s.commit()
    return True


def list_cheques(status=None, direction=None):
    s = get_session()
    _ensure(s)
    q = s.query(Cheque)
    if status:
        q = q.filter(Cheque.status == status)
    if direction:
        q = q.filter(Cheque.direction == direction)
    out = []
    for c in q.order_by(Cheque.cheque_date).all():
        out.append({"id": c.id, "party": c.party, "bank": c.bank,
                    "cheque_no": c.cheque_no, "amount": c.amount,
                    "date": str(c.cheque_date),
                    "direction": c.direction, "status": c.status})
    return out


def post_dated(as_on=None):
    ref = _d(as_on) or date.today()
    out = []
    for r in list_cheques(status="Pending"):
        d = _d(r["date"])
        if d and d > ref:
            out.append(r)
    return out


def print_cheque(cheque_id, path=None):
    s = get_session()
    _ensure(s)
    c = s.get(Cheque, cheque_id)
    if not c:
        return None
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except Exception:
        return "LIB_MISSING"
    path = path or os.path.join(os.getcwd(), "output",
                                "cheque_%d.pdf" % c.id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 120
    cv.setFont("Helvetica", 11)
    cv.drawString(60, y, "Date: %s" % c.cheque_date)
    cv.drawString(360, y, "Cheque No: %s" % (c.cheque_no or ""))
    cv.drawString(60, y - 40, "Pay: %s" % (c.party or ""))
    cv.drawString(60, y - 70, "Amount: %.2f" % (c.amount or 0))
    cv.drawString(60, y - 100, "Rupees %.2f only" % (c.amount or 0))
    cv.save()
    return path