# services/orders.py
"""Order processing: quotations, sales/purchase orders, delivery challans, and
converting an order into an actual invoice. Built on Order/OrderItem plus the
existing trading service.
"""
from datetime import date as _date

from db.engine import get_session
from db.models import NumberSeries, Ledger, Item
from db.models_orders import Order, OrderItem
from services import trading

# document numbering per (otype, stage)
_PREFIX = {
    ("Sales", "Quotation"): ("SalesQuotation", "QTN/"),
    ("Sales", "Order"): ("SalesOrder", "SO/"),
    ("Sales", "Challan"): ("SalesChallan", "DC/"),
    ("Purchase", "Quotation"): ("PurchaseQuotation", "PQT/"),
    ("Purchase", "Order"): ("PurchaseOrder", "PO/"),
    ("Purchase", "Challan"): ("PurchaseChallan", "PDC/"),
}


def _next_doc_no(s, otype, stage):
    vtype, prefix = _PREFIX.get((otype, stage), ("Order", "ORD/"))
    ns = s.query(NumberSeries).filter_by(vtype=vtype).first()
    if not ns:
        ns = NumberSeries(vtype=vtype, prefix=prefix, next_no=1, width=4)
        s.add(ns)
        s.flush()
    number = f"{ns.prefix}{str(ns.next_no).zfill(ns.width or 4)}"
    ns.next_no = (ns.next_no or 1) + 1
    return number


def list_parties():
    s = get_session()
    try:
        rows = (s.query(Ledger).filter(Ledger.is_party == True)  # noqa: E712
                .order_by(Ledger.name).all())
        return [{"id": l.id, "name": l.name} for l in rows]
    finally:
        s.close()


def list_items():
    s = get_session()
    try:
        rows = s.query(Item).order_by(Item.name).all()
        return [{"id": i.id, "name": i.name, "rate": i.sale_rate or 0,
                 "purchase_rate": i.purchase_rate or 0,
                 "gst_rate": i.gst_rate or 0} for i in rows]
    finally:
        s.close()


def create_order(otype, stage, party_id, lines, vdate=None, narration=None):
    """lines = [{item_id, qty, rate, gst_rate}]. Returns the new document no."""
    if not lines:
        raise ValueError("Add at least one item line.")
    s = get_session()
    try:
        number = _next_doc_no(s, otype, stage)
        total = 0.0
        o = Order(otype=otype, stage=stage, number=number,
                  date=vdate or _date.today(), party_id=party_id or None,
                  narration=narration, status="Open")
        s.add(o)
        s.flush()
        for ln in lines:
            qty = float(ln.get("qty") or 0)
            rate = float(ln.get("rate") or 0)
            gst = float(ln.get("gst_rate") or 0)
            amount = round(qty * rate, 2)
            total += amount + round(amount * gst / 100.0, 2)
            s.add(OrderItem(order_id=o.id, item_id=int(ln["item_id"]),
                            qty=qty, rate=rate, gst_rate=gst, amount=amount))
        o.total = round(total, 2)
        s.commit()
        return number
    finally:
        s.close()


def list_orders(otype=None, stage=None, status=None):
    s = get_session()
    try:
        pmap = {l.id: l.name for l in s.query(Ledger).all()}
        q = s.query(Order)
        if otype:
            q = q.filter(Order.otype == otype)
        if stage:
            q = q.filter(Order.stage == stage)
        if status:
            q = q.filter(Order.status == status)
        out = []
        for o in q.order_by(Order.date, Order.id).all():
            out.append({"id": o.id, "Date": str(o.date), "Number": o.number,
                        "Type": o.otype, "Stage": o.stage,
                        "Party": pmap.get(o.party_id, ""),
                        "Total": round(o.total or 0, 2), "Status": o.status})
        return out
    finally:
        s.close()


def pending_orders(otype):
    """Orders with quantity still to be invoiced."""
    s = get_session()
    try:
        pmap = {l.id: l.name for l in s.query(Ledger).all()}
        inames = {i.id: i.name for i in s.query(Item).all()}
        out = []
        q = (s.query(Order).filter(Order.otype == otype,
             Order.stage.in_(["Order", "Quotation"]),
             Order.status != "Closed").order_by(Order.date, Order.id))
        for o in q.all():
            for it in o.items:
                pend = round((it.qty or 0) - (it.invoiced_qty or 0), 2)
                if pend > 0.0001:
                    out.append({"Number": o.number, "Date": str(o.date),
                                "Party": pmap.get(o.party_id, ""),
                                "Item": inames.get(it.item_id, it.item_id),
                                "Ordered": it.qty,
                                "Invoiced": it.invoiced_qty,
                                "Pending": pend})
        return out
    finally:
        s.close()


def convert_to_invoice(order_id):
    """Turn an order's pending quantities into a Sales Invoice or Purchase."""
    s = get_session()
    try:
        o = s.get(Order, order_id)
        if not o:
            raise ValueError("Order not found.")
        otype = o.otype
        party_id = o.party_id
        note = f"From {o.stage} {o.number}"
        lines = []
        for it in o.items:
            pend = round((it.qty or 0) - (it.invoiced_qty or 0), 2)
            if pend > 0.0001:
                lines.append({"item_id": it.item_id, "qty": pend,
                              "rate": it.rate, "gst_rate": it.gst_rate})
        if not lines:
            raise ValueError("Nothing pending to invoice on this order.")
    finally:
        s.close()

    if otype == "Sales":
        v = trading.create_sales_invoice(party_id, lines, narration=note)
    else:
        v = trading.create_purchase(party_id, lines, narration=note)

    s2 = get_session()
    try:
        o2 = s2.get(Order, order_id)
        for it in o2.items:
            it.invoiced_qty = it.qty
        o2.status = "Closed"
        s2.commit()
    finally:
        s2.close()
    return getattr(v, "number", "")