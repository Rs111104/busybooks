# tests/test_trial_balance.py
from sqlalchemy import func
from core.posting import post_voucher
from db.models import VoucherEntry


def test_trial_balance_ties_out(session, masters):
    entries = [
        {"ledger_id": masters["party"].id, "debit": 1180, "credit": 0},
        {"ledger_id": masters["sales"].id, "debit": 0, "credit": 1000},
        {"ledger_id": masters["cgst"].id, "debit": 0, "credit": 90},
        {"ledger_id": masters["sgst"].id, "debit": 0, "credit": 90},
    ]
    post_voucher(session, "Sales", entries, party_id=masters["party"].id)

    total_debit = session.query(func.sum(VoucherEntry.debit)).scalar() or 0
    total_credit = session.query(func.sum(VoucherEntry.credit)).scalar() or 0
    assert round(total_debit, 2) == round(total_credit, 2)