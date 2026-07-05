# services/item_ledger.py -- per-item stock movement with running balance
from db.engine import get_session
from db.models import StockLedger, Item, Voucher


def list_items():
    s = get_session()
    return [(i.id, i.name) for i in s.query(Item).order_by(Item.name).all()]


def item_ledger(item_id):
    s = get_session()
    rows = (s.query(StockLedger)
            .filter(StockLedger.item_id == item_id)
            .order_by(StockLedger.date, StockLedger.id).all())
    out, bal = [], 0.0
    for r in rows:
        qin = r.qty_in or 0
        qout = r.qty_out or 0
        bal += qin - qout
        v = s.get(Voucher, r.voucher_id) if r.voucher_id else None
        out.append({
            "date": str(r.date) if r.date else "",
            "voucher": (v.number if v else "") or "",
            "in": qin, "out": qout, "balance": bal,
            "rate": r.rate or 0, "value": r.value or 0,
        })
    return out