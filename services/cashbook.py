# services/cashbook.py -- cash/bank book with running balance
from db.engine import get_session
from db.models import VoucherEntry, Voucher, Ledger


def _cashish(l):
    name = (l.name or "").lower()
    return ("cash" in name) or ("bank" in name)


def cash_bank_ledgers():
    s = get_session()
    return [(l.id, l.name)
            for l in s.query(Ledger).order_by(Ledger.name).all()
            if _cashish(l)]


def cashbook(ledger_id):
    s = get_session()
    entries = (s.query(VoucherEntry)
               .filter(VoucherEntry.ledger_id == ledger_id).all())

    def vkey(e):
        v = s.get(Voucher, e.voucher_id) if e.voucher_id else None
        return (str(v.date) if v and v.date else "", e.id)
    entries.sort(key=vkey)

    out, bal = [], 0.0
    for e in entries:
        v = s.get(Voucher, e.voucher_id) if e.voucher_id else None
        dr = e.debit or 0
        cr = e.credit or 0
        bal += dr - cr
        out.append({
            "date": str(v.date) if v and v.date else "",
            "voucher": (v.number if v else "") or "",
            "type": (v.vtype if v else "") or "",
            "debit": dr, "credit": cr, "balance": bal,
        })
    return out