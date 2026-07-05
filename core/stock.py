# core/stock.py
"""Stock movements + valuation with a hard negative-stock guard."""
from db.models import StockLedger, Item


class NegativeStockError(Exception):
    """Raised when an outward movement would drive stock below zero."""


def _opening_qty(session, item_id):
    it = session.get(Item, item_id)
    return (it.opening_qty or 0) if it else 0


def current_qty(session, item_id, godown_id=None):
    q = session.query(StockLedger).filter_by(item_id=item_id)
    if godown_id is not None:
        q = q.filter_by(godown_id=godown_id)
    total = _opening_qty(session, item_id) if godown_id is None else 0
    for row in q.all():
        total += (row.qty_in or 0) - (row.qty_out or 0)
    return round(total, 4)


def record_movement(session, item_id, qty_in, qty_out, rate, godown_id,
                    voucher_id, mdate, allow_negative=False):
    qty_in = qty_in or 0
    qty_out = qty_out or 0
    if qty_in < 0 or qty_out < 0:
        raise ValueError("Stock quantities cannot be negative.")
    if qty_out and not allow_negative:
        available = current_qty(session, item_id)
        if qty_out > available + 1e-9:
            it = session.get(Item, item_id)
            name = it.name if it else f"#{item_id}"
            raise NegativeStockError(
                f"Not enough stock for '{name}': have {available}, "
                f"trying to remove {qty_out}."
            )
    value = round((qty_in - qty_out) * (rate or 0), 2)
    row = StockLedger(
        item_id=item_id, godown_id=godown_id, voucher_id=voucher_id,
        date=mdate, qty_in=qty_in, qty_out=qty_out, rate=rate or 0,
        value=value,
    )
    session.add(row)
    session.flush()
    return row


def avg_cost(session, item_id):
    """Weighted-average cost from opening + all inward movements."""
    it = session.get(Item, item_id)
    total_qty = (it.opening_qty or 0) if it else 0
    total_val = ((it.opening_qty or 0) * (it.opening_rate or 0)) if it else 0
    for row in session.query(StockLedger).filter_by(item_id=item_id).all():
        if (row.qty_in or 0) > 0:
            total_qty += row.qty_in
            total_val += (row.qty_in or 0) * (row.rate or 0)
    if total_qty <= 0:
        return round(((it.opening_rate or 0) if it else 0), 4)
    return round(total_val / total_qty, 4)


def stock_value(session):
    """Total closing stock value at weighted-average cost."""
    total = 0.0
    for it in session.query(Item).all():
        total += current_qty(session, it.id) * avg_cost(session, it.id)
    return round(total, 2)


def summary(session):
    rows = []
    for it in session.query(Item).all():
        qty = current_qty(session, it.id)
        cost = avg_cost(session, it.id)
        rows.append({
            "item_id": it.id, "name": it.name, "qty": qty,
            "rate": cost, "value": round(qty * cost, 2),
        })
    return rows