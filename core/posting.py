# core/posting.py
"""Double-entry posting engine.

Guarantees: debits == credits, a voucher number is assigned atomically
(only consumed on a successful commit), stock is recorded for item lines,
and the whole thing commits as ONE transaction or rolls back cleanly.
"""
from datetime import date as _date

from core.numbering import next_number
from core import stock as stock_mod
from db.models import Voucher, VoucherEntry, VoucherItem

# Vouchers whose item lines INCREASE stock (goods coming in)
_INWARD = {"Purchase", "PurchaseReturn", "CreditNote", "Production", "StockIn"}
# Vouchers whose item lines DECREASE stock (goods going out)
_OUTWARD = {"Sales", "SalesReturn", "DebitNote", "Consumption", "StockOut"}

_ROUND_TOL = 0.01  # 1 paisa tolerance for float rounding


def _r2(x):
    return round((x or 0) + 0.0, 2)


def post_voucher(session, vtype, entries, vdate=None, party_id=None,
                 narration=None, items=None, allow_negative=False):
    """Create a fully-validated double-entry voucher.

    entries: list of {"ledger_id": int, "debit": float, "credit": float}
    items:   optional list of {"item_id","qty","rate","amount","gst_rate",
             "cgst","sgst","igst","godown_id"}
    Returns the committed Voucher (with .number).
    """
    if not vtype:
        raise ValueError("Voucher type is required.")
    entries = entries or []
    if not entries:
        raise ValueError("A voucher needs at least one ledger entry.")

    # ---- validate every entry ----
    total_debit = 0.0
    total_credit = 0.0
    for e in entries:
        if e.get("ledger_id") is None:
            raise ValueError("Every entry must reference a ledger.")
        d = e.get("debit") or 0
        c = e.get("credit") or 0
        if d < 0 or c < 0:
            raise ValueError("Debit/credit amounts cannot be negative.")
        if d and c:
            raise ValueError(
                "An entry cannot carry both a debit and a credit.")
        total_debit += d
        total_credit += c

    # ---- the golden rule: debits must equal credits ----
    if abs(total_debit - total_credit) > _ROUND_TOL:
        raise ValueError(
            f"Voucher does not balance: debit {_r2(total_debit)} "
            f"!= credit {_r2(total_credit)}."
        )

    vdate = vdate or _date.today()

    try:
        number = next_number(session, vtype)
        v = Voucher(
            vtype=vtype, number=number, date=vdate, party_id=party_id,
            narration=narration, total=_r2(total_debit),
        )
        session.add(v)
        session.flush()  # assigns v.id

        for e in entries:
            session.add(VoucherEntry(
                voucher_id=v.id, ledger_id=e["ledger_id"],
                debit=_r2(e.get("debit")), credit=_r2(e.get("credit")),
            ))

        for it in (items or []):
            qty = it.get("qty") or 0
            rate = it.get("rate") or 0
            amount = it.get("amount")
            if amount is None:
                amount = qty * rate
            session.add(VoucherItem(
                voucher_id=v.id, item_id=it["item_id"],
                godown_id=it.get("godown_id"), qty=qty, rate=rate,
                amount=_r2(amount), gst_rate=it.get("gst_rate") or 0,
                cgst=_r2(it.get("cgst")), sgst=_r2(it.get("sgst")),
                igst=_r2(it.get("igst")),
            ))
            if vtype in _INWARD:
                stock_mod.record_movement(
                    session, it["item_id"], qty, 0, rate,
                    it.get("godown_id"), v.id, vdate,
                    allow_negative=allow_negative)
            elif vtype in _OUTWARD:
                stock_mod.record_movement(
                    session, it["item_id"], 0, qty, rate,
                    it.get("godown_id"), v.id, vdate,
                    allow_negative=allow_negative)

        session.commit()
        return v
    except Exception:
        session.rollback()
        raise