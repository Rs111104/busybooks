# tests/test_posting.py
import pytest
from core.posting import post_voucher
from core.numbering import peek_number


def _sales_entries(m):
    return [
        {"ledger_id": m["party"].id, "debit": 1180, "credit": 0},
        {"ledger_id": m["sales"].id, "debit": 0, "credit": 1000},
        {"ledger_id": m["cgst"].id, "debit": 0, "credit": 90},
        {"ledger_id": m["sgst"].id, "debit": 0, "credit": 90},
    ]


def test_balanced_posts(session, masters):
    v = post_voucher(session, "Sales", _sales_entries(masters),
                     party_id=masters["party"].id)
    assert v.number
    assert v.total == 1180


def test_unbalanced_rejected(session, masters):
    bad = [
        {"ledger_id": masters["party"].id, "debit": 1180, "credit": 0},
        {"ledger_id": masters["sales"].id, "debit": 0, "credit": 1000},
    ]
    with pytest.raises(ValueError):
        post_voucher(session, "Sales", bad)


def test_failed_post_burns_no_number(session, masters):
    before = peek_number(session, "Sales")
    bad = [{"ledger_id": masters["party"].id, "debit": 100, "credit": 0}]
    with pytest.raises(ValueError):
        post_voucher(session, "Sales", bad)   # unbalanced -> rollback
    assert peek_number(session, "Sales") == before