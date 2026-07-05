# services/bank.py
"""Bank reconciliation. For a chosen ledger, list its entries with a running
book balance, and let the user mark which have 'cleared' the bank. Cleared
entry ids are saved per-ledger in settings.json.
"""
from db.engine import get_session
from db.models import Ledger, VoucherEntry, Voucher
from utils.settings import get_setting, set_setting


def ledger_names():
    s = get_session()
    try:
        return [l.name for l in s.query(Ledger).order_by(Ledger.name).all()]
    finally:
        s.close()


def _cleared_map():
    return get_setting("cleared", {}) or {}


def toggle_cleared(ledger_name, entry_id, cleared):
    data = _cleared_map()
    ids = set(data.get(ledger_name, []))
    if cleared:
        ids.add(entry_id)
    else:
        ids.discard(entry_id)
    data[ledger_name] = sorted(ids)
    set_setting("cleared", data)


def statement(ledger_name):
    s = get_session()
    try:
        l = s.query(Ledger).filter_by(name=ledger_name).one_or_none()
        if not l:
            return {"rows": [], "book_balance": 0.0, "cleared_balance": 0.0}
        rows = (s.query(VoucherEntry, Voucher)
                .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
                .filter(VoucherEntry.ledger_id == l.id)
                .order_by(Voucher.date, Voucher.id).all())
        cleared_ids = set(_cleared_map().get(ledger_name, []))
        opening = (l.opening_balance or 0) if (l.opening_dc or "Dr") == "Dr" \
            else -(l.opening_balance or 0)
        book = opening
        cleared_bal = opening
        out = []
        for e, v in rows:
            delta = (e.debit or 0) - (e.credit or 0)
            book += delta
            cl = e.id in cleared_ids
            if cl:
                cleared_bal += delta
            out.append({"id": e.id, "date": str(v.date),
                        "voucher": f"{v.vtype} {v.number}",
                        "debit": e.debit, "credit": e.credit, "cleared": cl})
        return {"rows": out, "book_balance": round(book, 2),
                "cleared_balance": round(cleared_bal, 2),
                "opening": round(opening, 2)}
    finally:
        s.close()