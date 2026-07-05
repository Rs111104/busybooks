# services/manufacturing.py
"""Manufacturing: define BOMs, check material shortages, and run production
that consumes raw materials and produces finished goods.
"""
from datetime import date as _date

from db.engine import get_session
from db.models import Item, Voucher, NumberSeries
from db.models_mfg import BOM, BOMComponent
from core import stock


def item_names():
    s = get_session()
    try:
        return [i.name for i in s.query(Item).order_by(Item.name).all()]
    finally:
        s.close()


def create_bom(name, product_item_name, output_qty=1.0, components=None):
    components = components or []
    s = get_session()
    try:
        if not (name or "").strip():
            raise ValueError("Enter a BOM name.")
        prod = s.query(Item).filter_by(name=product_item_name).first()
        if not prod:
            raise ValueError("Unknown finished product.")
        b = BOM(name=name.strip(), product_item_id=prod.id,
                output_qty=float(output_qty or 1))
        s.add(b)
        s.flush()
        for c in components:
            it = s.query(Item).filter_by(name=c["item_name"]).first()
            if not it:
                raise ValueError(f"Unknown component: {c['item_name']}")
            s.add(BOMComponent(bom_id=b.id, item_id=it.id,
                               qty=float(c["qty"] or 0)))
        s.commit()
        return b.id
    finally:
        s.close()


def list_boms():
    s = get_session()
    try:
        inames = {i.id: i.name for i in s.query(Item).all()}
        out = []
        for b in s.query(BOM).order_by(BOM.name).all():
            out.append({"id": b.id, "Name": b.name,
                        "Product": inames.get(b.product_item_id, "?"),
                        "Output qty": b.output_qty,
                        "Components": len(b.components)})
        return out
    finally:
        s.close()


def bom_detail(bom_id):
    s = get_session()
    try:
        b = s.get(BOM, bom_id)
        if not b:
            return None
        inames = {i.id: i.name for i in s.query(Item).all()}
        comps = [{"Item": inames.get(c.item_id, "?"), "Qty per batch": c.qty}
                 for c in b.components]
        return {"id": b.id, "name": b.name,
                "product": inames.get(b.product_item_id, "?"),
                "output_qty": b.output_qty, "components": comps}
    finally:
        s.close()


def check_shortage(bom_id, times=1):
    """Return components whose required qty exceeds current stock."""
    times = float(times or 1)
    s = get_session()
    try:
        b = s.get(BOM, bom_id)
        if not b:
            raise ValueError("Unknown BOM.")
        inames = {i.id: i.name for i in s.query(Item).all()}
        out = []
        for c in b.components:
            need = (c.qty or 0) * times
            have = stock.current_qty(s, c.item_id)
            if need > have:
                out.append({"Item": inames.get(c.item_id, "?"),
                            "Required": need, "In stock": have,
                            "Short by": round(need - have, 3)})
        return out
    finally:
        s.close()


def produce(bom_id, times=1, allow_negative=False, vdate=None):
    """Run production `times` batches: consume components, add finished goods.
    Returns (voucher_number, finished_unit_cost).
    """
    times = float(times or 1)
    if times <= 0:
        raise ValueError("Batches to produce must be greater than zero.")
    s = get_session()
    try:
        b = s.get(BOM, bom_id)
        if not b:
            raise ValueError("Unknown BOM.")
        # shortage guard
        if not allow_negative:
            for c in b.components:
                need = (c.qty or 0) * times
                if need > stock.current_qty(s, c.item_id):
                    raise ValueError(
                        "Not enough raw materials. Check shortage first "
                        "or tick 'Allow negative stock'.")
        # number series
        ns = s.query(NumberSeries).filter_by(vtype="Production").first()
        if not ns:
            ns = NumberSeries(vtype="Production", prefix="MFG/", next_no=1,
                              width=4)
            s.add(ns)
            s.flush()
        number = f"{ns.prefix}{str(ns.next_no).zfill(ns.width or 4)}"
        ns.next_no = (ns.next_no or 1) + 1
        v = Voucher(vtype="Production", number=number,
                    date=vdate or _date.today(),
                    narration=f"Production via BOM {b.name}", total=0.0)
        s.add(v)
        s.flush()
        # consume components at their purchase rate; roll up total cost
        total_cost = 0.0
        for c in b.components:
            it = s.get(Item, c.item_id)
            rate = it.purchase_rate or it.sale_rate or 0.0
            qty = (c.qty or 0) * times
            total_cost += rate * qty
            stock.record_movement(s, c.item_id, 0.0, qty, rate, None, v.id,
                                   v.date)
        # add finished goods
        made = (b.output_qty or 1) * times
        unit_cost = round(total_cost / made, 4) if made else 0.0
        stock.record_movement(s, b.product_item_id, made, 0.0, unit_cost,
                               None, v.id, v.date)
        v.total = round(total_cost, 2)
        s.commit()
        return number, unit_cost
    finally:
        s.close()