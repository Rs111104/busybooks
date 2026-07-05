# core/gst.py
"""GST logic: split a tax amount into CGST+SGST (local) or IGST (inter-state).
Rule: if the party's state is different from the company's state, it's
inter-state (IGST). Otherwise it's local (CGST + SGST, each half the rate).
"""


def is_inter_state(company_state_code, party_state_code):
    if not company_state_code or not party_state_code:
        return False
    return str(company_state_code).strip() != str(party_state_code).strip()


def split_gst(amount, gst_rate, inter_state):
    """Return {'cgst','sgst','igst'} for a taxable amount at gst_rate %."""
    amount = round(float(amount or 0), 2)
    rate = float(gst_rate or 0)
    tax = round(amount * rate / 100.0, 2)
    if inter_state:
        return {"cgst": 0.0, "sgst": 0.0, "igst": tax}
    half = round(tax / 2.0, 2)
    return {"cgst": half, "sgst": round(tax - half, 2), "igst": 0.0}