# services/aging.py -- receivables & payables aging (FIFO bill-by-bill)
from datetime import date, datetime
from db.engine import get_session
from db.models import Ledger, VoucherEntry, Voucher

_BUCKETS = [(0, 30), (31, 60), (61, 90), (91, 10 ** 9)]
LABELS = ["0-30", "31-60", "61-90", "90+"]


def _as_date(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
    except Exception:
        return date.today()


def _open_items(s, ledger, receivable):
    # receivable: invoices = debits, payments = credits (customer owes us)
    # payable:    invoices = credits, payments = debits (we owe supplier)
    entries = []
    for e in (s.query(VoucherEntry)
              .filter(VoucherEntry.ledger_id == ledger.id).all()):
        v = s.get(Voucher, e.voucher_id) if e.voucher_id else None
        d = _as_date(v.date) if (v and v.date) else date.today()
        inv = (e.debit or 0) if receivable else (e.credit or 0)
        pay = (e.credit or 0) if receivable else (e.debit or 0)
        entries.append((d, inv, pay))
    ob = ledger.opening_balance or 0
    if ob:
        is_dr = (ledger.opening_dc or "Dr") == "Dr"
        op_inv = ob if (is_dr == receivable) else 0
        op_pay = 0 if (is_dr == receivable) else ob
        entries.insert(0, (date(1900, 1, 1), op_inv, op_pay))
    entries.sort(key=lambda r: r[0])

    invoices = []
    pool = 0.0
    for d, inv, pay in entries:
        pool += pay
        if inv:
            invoices.append([d, inv])
        i = 0
        while pool > 1e-9 and i < len(invoices):
            take = min(invoices[i][1], pool)
            invoices[i][1] -= take
            pool -= take
            i += 1
    return [x for x in invoices if x[1] > 0.01]


def _aging(receivable, as_on=None):
    s = get_session()
    today = _as_date(as_on) if as_on else date.today()
    out = []
    for l in s.query(Ledger).filter(Ledger.is_party.is_(True)).all():
        items = _open_items(s, l, receivable)
        if not items:
            continue
        b = [0.0, 0.0, 0.0, 0.0]
        total = 0.0
        for d, amt in items:
            age = (today - d).days
            if age < 0:
                age = 0
            total += amt
            for idx, (lo, hi) in enumerate(_BUCKETS):
                if lo <= age <= hi:
                    b[idx] += amt
                    break
        out.append({
            "party": l.name, "total": round(total, 2),
            "b0": round(b[0], 2), "b1": round(b[1], 2),
            "b2": round(b[2], 2), "b3": round(b[3], 2),
        })
    out.sort(key=lambda r: r["total"], reverse=True)
    return out


def receivable_aging(as_on=None):
    return _aging(True, as_on)


def payable_aging(as_on=None):
    return _aging(False, as_on)