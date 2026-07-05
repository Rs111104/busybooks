# services/mrp.py -- MRP / tax-inclusive (reverse-charge) billing helper
def breakup(mrp, gst_rate, inter_state=False):
    """Reverse-calc a GST-inclusive MRP into taxable + tax parts."""
    mrp = float(mrp or 0)
    rate = float(gst_rate or 0)
    taxable = round(mrp * 100.0 / (100.0 + rate), 2) if rate else round(mrp, 2)
    tax = round(mrp - taxable, 2)
    if inter_state:
        igst, cgst, sgst = tax, 0.0, 0.0
    else:
        cgst = round(tax / 2.0, 2)
        sgst = round(tax - cgst, 2)
        igst = 0.0
    return {"mrp": round(mrp, 2), "taxable": taxable, "cgst": cgst,
            "sgst": sgst, "igst": igst, "tax": tax, "gross": round(mrp, 2)}


def line_from_mrp(mrp, qty, gst_rate, inter_state=False):
    """Multiply a unit MRP breakup across a quantity."""
    qty = float(qty or 0)
    u = breakup(mrp, gst_rate, inter_state)
    return {"qty": qty, "mrp": u["mrp"],
            "taxable": round(u["taxable"] * qty, 2),
            "cgst": round(u["cgst"] * qty, 2),
            "sgst": round(u["sgst"] * qty, 2),
            "igst": round(u["igst"] * qty, 2),
            "gross": round(u["gross"] * qty, 2)}