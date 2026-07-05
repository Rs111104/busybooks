"""Trading documents: sales, purchase, credit note, debit note.

Each one auto-splits GST, posts a balanced double-entry voucher, and
records stock movement. Item lines look like:

    {"item_id": 1, "qty": 2, "rate": 100, "gst_rate": 18}

Stock is recorded exactly ONCE, inside post_voucher(), from the items
payload. This module must NOT also call stock.record_movement() or the
quantity would be double-counted.
"""

from db.engine import get_session
from db.models import Ledger, Company
from core.posting import post_voucher
from core.gst import split_gst, is_inter_state


def _ledger_id(session, name):
    l = session.query(Ledger).filter_by(name=name).one_or_none()
    if not l:
        raise ValueError(f"Required ledger '{name}' is missing. "
                         "Re-seed the company (delete its .db and re-run).")
    return l.id


def _company_state_code(session):
    c = session.query(Company).first()
    return c.state_code if c else None


def _party_state_code(session, party_id):
    p = session.get(Ledger, party_id)
    return p.state_code if p else None


def _compute(session, lines, inter_state):
    """Turn raw lines into detailed lines + totals."""
    detailed, sub, cg, sg, ig = [], 0.0, 0.0, 0.0, 0.0
    for ln in lines:
        qty = round(float(ln.get("qty") or 0), 3)
        rate = round(float(ln.get("rate") or 0), 2)
        gst_rate = float(ln.get("gst_rate") or 0)
        amount = round(qty * rate, 2)
        tax = split_gst(amount, gst_rate, inter_state)
        detailed.append({"item_id": ln["item_id"], "qty": qty, "rate": rate,
                         "amount": amount, "gst_rate": gst_rate,
                         "cgst": tax["cgst"], "sgst": tax["sgst"],
                         "igst": tax["igst"]})
        sub += amount
        cg += tax["cgst"]
        sg += tax["sgst"]
        ig += tax["igst"]
    totals = {"sub": round(sub, 2), "cgst": round(cg, 2), "sgst": round(sg, 2),
              "igst": round(ig, 2)}
    totals["grand"] = round(sub + cg + sg + ig, 2)
    return detailed, totals


def _gst_entries(session, totals, inter_state, output):
    """Build the GST ledger entries. output=True -> Output GST (sales side)."""
    suffix = "Output" if output else "Input"
    rows = []
    if inter_state:
        if totals["igst"]:
            rows.append((f"IGST {suffix}", totals["igst"]))
    else:
        if totals["cgst"]:
            rows.append((f"CGST {suffix}", totals["cgst"]))
        if totals["sgst"]:
            rows.append((f"SGST {suffix}", totals["sgst"]))
    return rows


def _items_payload(detailed):
    return [{"item_id": d["item_id"], "qty": d["qty"], "rate": d["rate"],
             "amount": d["amount"], "gst_rate": d["gst_rate"],
             "cgst": d["cgst"], "sgst": d["sgst"], "igst": d["igst"]}
            for d in detailed]


def _run(vtype, party_id, lines, vdate, narration, builder):
    """Shared runner. builder(session, party_id, det, totals, inter) -> entries.

    Stock movements are recorded by post_voucher() from the items payload
    (it knows inward vs outward from the voucher type), so this runner does
    NOT call stock.record_movement() itself -- doing so double-counted qty.
    """
    s = get_session()
    try:
        inter = is_inter_state(_company_state_code(s),
                               _party_state_code(s, party_id))
        det, totals = _compute(s, lines, inter)
        entries = builder(s, party_id, det, totals, inter)
        v = post_voucher(s, vtype, entries, vdate=vdate, party_id=party_id,
                         narration=narration, items=_items_payload(det))
        return v.number
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# ---------------- Sales: Dr Party / Cr Sales + Cr Output GST ---------------
def create_sales_invoice(party_id, lines, vdate=None, narration=None):
    def build(s, pid, det, t, inter):
        e = [{"ledger_id": pid, "debit": t["grand"], "credit": 0},
             {"ledger_id": _ledger_id(s, "Sales"), "debit": 0,
              "credit": t["sub"]}]
        for name, amt in _gst_entries(s, t, inter, output=True):
            e.append({"ledger_id": _ledger_id(s, name), "debit": 0,
                      "credit": amt})
        return e
    return _run("Sales", party_id, lines, vdate, narration, build)


# ------------- Purchase: Dr Purchase + Dr Input GST / Cr Party --------------
def create_purchase(party_id, lines, vdate=None, narration=None):
    def build(s, pid, det, t, inter):
        e = [{"ledger_id": _ledger_id(s, "Purchase"), "debit": t["sub"],
              "credit": 0}]
        for name, amt in _gst_entries(s, t, inter, output=False):
            e.append({"ledger_id": _ledger_id(s, name), "debit": amt,
                      "credit": 0})
        e.append({"ledger_id": pid, "debit": 0, "credit": t["grand"]})
        return e
    return _run("Purchase", party_id, lines, vdate, narration, build)


# --- Credit Note (sales return): Dr Sales + Dr Output GST / Cr Party --------
def create_credit_note(party_id, lines, vdate=None, narration=None):
    def build(s, pid, det, t, inter):
        e = [{"ledger_id": _ledger_id(s, "Sales"), "debit": t["sub"],
              "credit": 0}]
        for name, amt in _gst_entries(s, t, inter, output=True):
            e.append({"ledger_id": _ledger_id(s, name), "debit": amt,
                      "credit": 0})
        e.append({"ledger_id": pid, "debit": 0, "credit": t["grand"]})
        return e
    # goods come back IN (post_voucher treats CreditNote as inward)
    return _run("CreditNote", party_id, lines, vdate, narration, build)


# --- Debit Note (purchase return): Dr Party / Cr Purchase + Cr Input GST ----
def create_debit_note(party_id, lines, vdate=None, narration=None):
    def build(s, pid, det, t, inter):
        e = [{"ledger_id": pid, "debit": t["grand"], "credit": 0},
             {"ledger_id": _ledger_id(s, "Purchase"), "debit": 0,
              "credit": t["sub"]}]
        for name, amt in _gst_entries(s, t, inter, output=False):
            e.append({"ledger_id": _ledger_id(s, name), "debit": 0,
                      "credit": amt})
        return e
    # goods go back OUT (post_voucher treats DebitNote as outward)
    return _run("DebitNote", party_id, lines, vdate, narration, build)