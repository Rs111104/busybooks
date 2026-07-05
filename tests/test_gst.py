# tests/test_gst.py
from core.gst import split_gst


def test_intra_state_18pct():
    r = split_gst(1000, 18, False)   # CGST 90 + SGST 90, IGST 0
    assert round(r["cgst"], 2) == 90.0
    assert round(r["sgst"], 2) == 90.0
    assert round(r["igst"], 2) == 0.0


def test_inter_state_18pct():
    r = split_gst(1000, 18, True)    # IGST 180, no CGST/SGST
    assert round(r["igst"], 2) == 180.0
    assert round(r["cgst"], 2) == 0.0
    assert round(r["sgst"], 2) == 0.0


def test_total_tax_5pct_rounding():
    r = split_gst(999, 5, False)     # total tax 49.95
    total = r["cgst"] + r["sgst"] + r["igst"]
    assert round(total, 2) == 49.95