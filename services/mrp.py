# services/mrp.py -- MRP / tax-inclusive price breakup
def breakup(mrp, gst_rate, inter_state=False):
    mrp = float(mrp or 0)
    rate = float(gst_rate or 0)
    taxable = round(mrp * 100.0 / (100.0 + rate), 2) if rate else mrp
    tax = round(mrp - taxable, 2)
    if inter_state:
        cgst = sgst = 0.0
        igst = tax
    else:
        cgst = sgst = round(tax / 2.0, 2)
        igst = 0.0
    return {"mrp": round(mrp, 2), "gst_rate": rate, "taxable": taxable,
            "cgst": cgst, "sgst": sgst, "igst": igst, "total_tax": tax}


def line_from_mrp(mrp, qty, gst_rate, inter_state=False):
    qty = float(qty or 0)
    one = breakup(mrp, gst_rate, inter_state)
    return {"qty": qty,
            "taxable": round(one["taxable"] * qty, 2),
            "cgst": round(one["cgst"] * qty, 2),
            "sgst": round(one["sgst"] * qty, 2),
            "igst": round(one["igst"] * qty, 2),
            "gross": round(one["mrp"] * qty, 2)}