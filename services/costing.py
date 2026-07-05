# services/costing.py
"""Cost centres, allocations, and budget-vs-actual reporting."""
from datetime import date as _date

from db.engine import get_session
from db.models import Ledger, Voucher, VoucherEntry
from db.models_costing import CostCentre, CostAllocation, Budget


def ledger_names():
    s = get_session()
    try:
        return [l.name for l in s.query(Ledger).order_by(Ledger.name).all()]
    finally:
        s.close()


# ---------- cost centres ----------
def create_cost_centre(name, parent_name=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a cost centre name.")
    s = get_session()
    try:
        if s.query(CostCentre).filter_by(name=name).first():
            raise ValueError("That cost centre already exists.")
        pid = None
        if parent_name:
            p = s.query(CostCentre).filter_by(name=parent_name).first()
            pid = p.id if p else None
        s.add(CostCentre(name=name, parent_id=pid))
        s.commit()
    finally:
        s.close()


def list_cost_centres():
    s = get_session()
    try:
        names = {c.id: c.name for c in s.query(CostCentre).all()}
        return [{"id": c.id, "Name": c.name,
                 "Parent": names.get(c.parent_id, "")}
                for c in s.query(CostCentre).order_by(CostCentre.name).all()]
    finally:
        s.close()


def cost_centre_names():
    s = get_session()
    try:
        return [c.name for c in
                s.query(CostCentre).order_by(CostCentre.name).all()]
    finally:
        s.close()


# ---------- allocations ----------
def allocate(cost_centre_name, ledger_name, amount, vdate=None):
    s = get_session()
    try:
        cc = s.query(CostCentre).filter_by(name=cost_centre_name).first()
        if not cc:
            raise ValueError("Unknown cost centre.")
        led = s.query(Ledger).filter_by(name=ledger_name).first()
        s.add(CostAllocation(cost_centre_id=cc.id,
                             ledger_id=led.id if led else None,
                             amount=float(amount or 0),
                             date=vdate or _date.today()))
        s.commit()
    finally:
        s.close()


def cost_centre_report():
    s = get_session()
    try:
        names = {c.id: c.name for c in s.query(CostCentre).all()}
        totals = {}
        for a in s.query(CostAllocation).all():
            totals[a.cost_centre_id] = totals.get(a.cost_centre_id, 0.0) \
                + (a.amount or 0)
        return [{"Cost centre": names.get(cid, "?"),
                 "Allocated": round(v, 2)} for cid, v in
                sorted(totals.items(), key=lambda x: names.get(x[0], ""))]
    finally:
        s.close()


# ---------- budgets ----------
def set_budget(ledger_name, period, amount):
    period = (period or "").strip()
    if len(period) != 7 or period[4] != "-":
        raise ValueError("Period must look like 2026-04 (YYYY-MM).")
    s = get_session()
    try:
        led = s.query(Ledger).filter_by(name=ledger_name).first()
        if not led:
            raise ValueError("Unknown ledger.")
        row = s.query(Budget).filter_by(ledger_id=led.id,
                                        period=period).first()
        if row:
            row.amount = float(amount or 0)
        else:
            s.add(Budget(ledger_id=led.id, period=period,
                         amount=float(amount or 0)))
        s.commit()
    finally:
        s.close()


def _actual_for(s, ledger_id, period):
    """Sum of movement (debit + credit) for a ledger in a YYYY-MM period."""
    total = 0.0
    q = (s.query(VoucherEntry, Voucher)
         .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
         .filter(VoucherEntry.ledger_id == ledger_id))
    for entry, v in q.all():
        if v.date and v.date.strftime("%Y-%m") == period:
            total += (entry.debit or 0) + (entry.credit or 0)
    return round(total, 2)


def budget_vs_actual(period):
    s = get_session()
    try:
        lnames = {l.id: l.name for l in s.query(Ledger).all()}
        out = []
        for b in s.query(Budget).filter_by(period=period).all():
            actual = _actual_for(s, b.ledger_id, period)
            out.append({"Ledger": lnames.get(b.ledger_id, "?"),
                        "Budget": round(b.amount or 0, 2), "Actual": actual,
                        "Variance": round((b.amount or 0) - actual, 2)})
        return out
    finally:
        s.close()