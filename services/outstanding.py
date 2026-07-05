# services/outstanding.py
"""Receivables & payables per party, with aging buckets by transaction date.
A party with a net debit balance owes YOU (receivable); a net credit balance
means YOU owe them (payable).
"""
from datetime import date
from db.engine import get_session
from db.models import Ledger, VoucherEntry, Voucher


def _bucket(days):
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def _rows(receivable=True):
    s = get_session()
    try:
        today = date.today()
        parties = s.query(Ledger).filter(Ledger.is_party == True).all()
        out = []
        for p in parties:
            entries = (s.query(VoucherEntry, Voucher)
                       .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
                       .filter(VoucherEntry.ledger_id == p.id).all())
            net = (p.opening_balance or 0) if (p.opening_dc or "Dr") == "Dr" \
                else -(p.opening_balance or 0)
            buckets = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
            for e, v in entries:
                amt = (e.debit or 0) - (e.credit or 0)
                net += amt
                try:
                    days = (today - v.date).days
                except Exception:
                    days = 0
                buckets[_bucket(days)] += amt
            if receivable and net > 0.01:
                bal = round(net, 2)
            elif (not receivable) and net < -0.01:
                bal = round(-net, 2)
                buckets = {k: -val for k, val in buckets.items()}
            else:
                continue
            out.append({"Party": p.name, "Balance": bal,
                        "0-30": round(buckets["0-30"], 2),
                        "31-60": round(buckets["31-60"], 2),
                        "61-90": round(buckets["61-90"], 2),
                        "90+": round(buckets["90+"], 2),
                        "Phone": p.phone or ""})
        return sorted(out, key=lambda x: -x["Balance"])
    finally:
        s.close()


def receivables():
    return _rows(True)


def payables():
    return _rows(False)