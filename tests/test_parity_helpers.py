# tests/test_parity_helpers.py -- unit tests for the 4 parity helpers
from services import gstin, mrp, report_columns as rc


def test_gstin_checksum_roundtrip():
    base = "27AAPFU0939F1Z"            # valid 14-char prefix
    good = base + gstin.check_digit(base)
    assert gstin.is_valid(good)
    wrong = base + ("A" if good[-1] != "A" else "B")
    assert not gstin.is_valid(wrong)
    assert not gstin.is_valid("NOTAGSTIN")


def test_mrp_breakup_intra():
    b = mrp.breakup(118, 18, inter_state=False)
    assert b["taxable"] == 100.0
    assert round(b["cgst"] + b["sgst"], 2) == 18.0
    assert b["igst"] == 0.0
    assert b["gross"] == 118.0


def test_mrp_breakup_inter():
    b = mrp.breakup(118, 18, inter_state=True)
    assert b["igst"] == 18.0
    assert b["cgst"] == 0.0


def test_report_columns_project():
    rows = [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]
    assert rc.project(rows, ["a", "c"]) == [[1, 3], [4, 6]]