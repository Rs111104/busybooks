# services/gst_returns.py
"""GST returns built from the tax already stored on each voucher item line.
GSTR-1 = outward supplies (Sales, minus Credit Notes) grouped by party GSTIN
and tax rate. GSTR-3B = a summary of output tax vs input credit.
"""
from db.engine import get_session
from db.models import Voucher, Ledger


def gstr1():
    """Party- and rate-wise outward supplies with tax split."""
    s = get_session()
    try:
        lmap = {l.id: l for l in s.query(Ledger).all()}
        rows = {}
        vs = s.query(Voucher).filter(
            Voucher.vtype.in_(["Sales", "CreditNote"])).all()
        for v in vs:
            party = lmap.get(v.party_id)
            gstin = (party.gstin if party else "") or "Unregistered"
            sign = -1 if v.vtype == "CreditNote" else 1
            for it in v.items:
                key = (gstin, it.gst_rate)
                r = rows.setdefault(key, {"GSTIN": gstin, "Rate%": it.gst_rate,
                                          "Taxable": 0.0, "CGST": 0.0,
                                          "SGST": 0.0, "IGST": 0.0})
                r["Taxable"] += sign * (it.amount or 0)
                r["CGST"] += sign * (it.cgst or 0)
                r["SGST"] += sign * (it.sgst or 0)
                r["IGST"] += sign * (it.igst or 0)
        out = []
        for r in rows.values():
            out.append({k: (round(val, 2) if isinstance(val, float) else val)
                        for k, val in r.items()})
        return sorted(out, key=lambda x: (str(x["GSTIN"]), x["Rate%"]))
    finally:
        s.close()


def gstr3b():
    """Summary: outward tax (sales) minus input tax (purchase) = net payable."""
    s = get_session()
    try:
        out = {"CGST": 0.0, "SGST": 0.0, "IGST": 0.0}
        inp = {"CGST": 0.0, "SGST": 0.0, "IGST": 0.0}
        taxable_out = 0.0
        taxable_in = 0.0
        for v in s.query(Voucher).all():
            if v.vtype in ("Sales", "CreditNote"):
                sign = -1 if v.vtype == "CreditNote" else 1
                for it in v.items:
                    taxable_out += sign * (it.amount or 0)
                    out["CGST"] += sign * (it.cgst or 0)
                    out["SGST"] += sign * (it.sgst or 0)
                    out["IGST"] += sign * (it.igst or 0)
            elif v.vtype in ("Purchase", "DebitNote"):
                sign = -1 if v.vtype == "DebitNote" else 1
                for it in v.items:
                    taxable_in += sign * (it.amount or 0)
                    inp["CGST"] += sign * (it.cgst or 0)
                    inp["SGST"] += sign * (it.sgst or 0)
                    inp["IGST"] += sign * (it.igst or 0)
        return [
            {"Section": "Outward taxable supplies (Sales)",
             "Taxable": round(taxable_out, 2), "CGST": round(out["CGST"], 2),
             "SGST": round(out["SGST"], 2), "IGST": round(out["IGST"], 2)},
            {"Section": "Inward supplies / ITC (Purchase)",
             "Taxable": round(taxable_in, 2), "CGST": round(inp["CGST"], 2),
             "SGST": round(inp["SGST"], 2), "IGST": round(inp["IGST"], 2)},
            {"Section": "NET GST PAYABLE", "Taxable": "",
             "CGST": round(out["CGST"] - inp["CGST"], 2),
             "SGST": round(out["SGST"] - inp["SGST"], 2),
             "IGST": round(out["IGST"] - inp["IGST"], 2)},
        ]
    finally:
        s.close()