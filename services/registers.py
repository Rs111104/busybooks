# services/registers.py -- Sales & Purchase registers
from db.engine import get_session
from db.models import Voucher, Ledger


def register(vtype):
    s = get_session()
    vs = (s.query(Voucher).filter(Voucher.vtype == vtype)
          .order_by(Voucher.date, Voucher.id).all())
    out, total = [], 0.0
    for v in vs:
        party = s.get(Ledger, v.party_id) if v.party_id else None
        amt = v.total or 0
        total += amt
        out.append({
            "date": str(v.date) if v.date else "",
            "number": v.number or "",
            "party": (party.name if party else "") or "",
            "amount": amt,
        })
    return out, total


def sales_register():
    return register("Sales")


def purchase_register():
    return register("Purchase")