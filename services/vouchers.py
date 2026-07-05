# services/vouchers.py
"""Create Payment / Receipt / Contra / Journal vouchers and list them.
Everything goes through core.posting.post_voucher, which refuses to save
unless total debits == total credits.
"""
from db.engine import get_session
from db.models import Voucher, Ledger
from core.posting import post_voucher

VOUCHER_TYPES = ["Payment", "Receipt", "Contra", "Journal"]


def list_ledger_options():
    """Return {name: id} for every ledger, for the dropdowns."""
    s = get_session()
    try:
        return {l.name: l.id for l in
                s.query(Ledger).order_by(Ledger.name).all()}
    finally:
        s.close()


def create_voucher(vtype, debit_id, credit_id, amount, vdate=None,
                   narration=None, party_id=None):
    """Post a simple two-line voucher: one account debited, one credited.
    Returns the auto-generated voucher number (e.g. 'PAY/0001').
    """
    amount = round(float(amount or 0), 2)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if debit_id == credit_id:
        raise ValueError("Debit and credit accounts must be different.")

    entries = [
        {"ledger_id": debit_id, "debit": amount, "credit": 0},
        {"ledger_id": credit_id, "debit": 0, "credit": amount},
    ]
    s = get_session()
    try:
        v = post_voucher(s, vtype, entries, vdate=vdate,
                         party_id=party_id, narration=narration)
        return v.number
    finally:
        s.close()


def list_recent_vouchers(limit=200):
    s = get_session()
    try:
        rows = (s.query(Voucher)
                .order_by(Voucher.id.desc()).limit(limit).all())
        return [{"id": v.id, "type": v.vtype, "number": v.number,
                 "date": str(v.date), "total": v.total,
                 "narration": v.narration or ""} for v in rows]
    finally:
        s.close()