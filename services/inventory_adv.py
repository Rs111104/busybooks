# services/inventory_adv.py
"""Advanced inventory: batch/lot with expiry, serial numbers, godown-to-godown
stock transfer, and expiry reporting.
"""
from datetime import date as _date, timedelta

from db.engine import get_session
from db.models import Item, Godown, Voucher, NumberSeries
from db.models_inventory import Batch, Serial
from core import stock


def item_names():
    s = get_session()
    try:
        return [i.name for i in s.query(Item).order_by(Item.name).all()]
    finally:
        s.close()


def godown_names():
    s = get_session()
    try:
        return [g.name for g in s.query(Godown).order_by(Godown.name).all()]
    finally:
        s.close()


def add_godown(name):
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a godown name.")
    s = get_session()
    try:
        if s.query(Godown).filter_by(name=name).first():
            raise ValueError("That godown already exists.")
        s.add(Godown(name=name))
        s.commit()
    finally:
        s.close()


def _parse_date(txt):
    txt = (txt or "").strip()
    if not txt:
        return None
    return _date.fromisoformat(txt)   # expects YYYY-MM-DD


# ---------- batches ----------
def add_batch(item_name, batch_no, qty, rate=0.0, mfg=None, expiry=None,
              godown_name=None):
    s = get_session()
    try:
        item = s.query(Item).filter_by(name=item_name).first()
        if not item:
            raise ValueError("Unknown item.")
        if not (batch_no or "").strip():
            raise ValueError("Enter a batch number.")
        gid = None
        if godown_name:
            g = s.query(Godown).filter_by(name=godown_name).first()
            gid = g.id if g else None
        b = Batch(item_id=item.id, batch_no=batch_no.strip(),
                  qty=float(qty or 0), rate=float(rate or 0),
                  mfg_date=_parse_date(mfg), expiry_date=_parse_date(expiry),
                  godown_id=gid)
        s.add(b)
        s.commit()
        return b.id
    finally:
        s.close()


def list_batches():
    s = get_session()
    try:
        inames = {i.id: i.name for i in s.query(Item).all()}
        out = []
        for b in s.query(Batch).order_by(Batch.expiry_date).all():
            out.append({"Item": inames.get(b.item_id, b.item_id),
                        "Batch": b.batch_no, "Qty": b.qty, "Rate": b.rate,
                        "Mfg": str(b.mfg_date or ""),
                        "Expiry": str(b.expiry_date or "")})
        return out
    finally:
        s.close()


def expiry_report(days=30):
    """Batches already expired or expiring within `days` days."""
    s = get_session()
    try:
        inames = {i.id: i.name for i in s.query(Item).all()}
        limit = _date.today() + timedelta(days=int(days))
        out = []
        rows = (s.query(Batch).filter(Batch.expiry_date != None)  # noqa: E711
                .order_by(Batch.expiry_date).all())
        for b in rows:
            if b.expiry_date <= limit and (b.qty or 0) > 0:
                d = (b.expiry_date - _date.today()).days
                out.append({"Item": inames.get(b.item_id, b.item_id),
                            "Batch": b.batch_no, "Qty": b.qty,
                            "Expiry": str(b.expiry_date), "Days left": d,
                            "Status": "EXPIRED" if d < 0 else "Expiring soon"})
        return out
    finally:
        s.close()


# ---------- serials ----------
def add_serials(item_name, serial_list):
    s = get_session()
    try:
        item = s.query(Item).filter_by(name=item_name).first()
        if not item:
            raise ValueError("Unknown item.")
        n = 0
        for sn in serial_list:
            sn = (sn or "").strip()
            if not sn:
                continue
            if s.query(Serial).filter_by(serial_no=sn).first():
                continue
            s.add(Serial(item_id=item.id, serial_no=sn, status="In Stock"))
            n += 1
        s.commit()
        return n
    finally:
        s.close()


def list_serials(status=None):
    s = get_session()
    try:
        inames = {i.id: i.name for i in s.query(Item).all()}
        q = s.query(Serial)
        if status:
            q = q.filter(Serial.status == status)
        return [{"Item": inames.get(x.item_id, x.item_id),
                 "Serial": x.serial_no, "Status": x.status}
                for x in q.order_by(Serial.item_id, Serial.serial_no).all()]
    finally:
        s.close()


# ---------- godown transfer ----------
def transfer_stock(item_name, from_godown, to_godown, qty, rate=0.0,
                   vdate=None):
    if from_godown == to_godown:
        raise ValueError("From and To godowns must differ.")
    s = get_session()
    try:
        item = s.query(Item).filter_by(name=item_name).first()
        if not item:
            raise ValueError("Unknown item.")
        gfrom = s.query(Godown).filter_by(name=from_godown).first()
        gto = s.query(Godown).filter_by(name=to_godown).first()
        if not gfrom or not gto:
            raise ValueError("Create both godowns first (Create godown).")
        ns = s.query(NumberSeries).filter_by(vtype="StockTransfer").first()
        if not ns:
            ns = NumberSeries(vtype="StockTransfer", prefix="ST/", next_no=1,
                              width=4)
            s.add(ns)
            s.flush()
        number = f"{ns.prefix}{str(ns.next_no).zfill(ns.width or 4)}"
        ns.next_no = (ns.next_no or 1) + 1
        v = Voucher(vtype="StockTransfer", number=number,
                    date=vdate or _date.today(),
                    narration=f"Transfer {item_name} {from_godown}->{to_godown}",
                    total=0.0)
        s.add(v)
        s.flush()
        q = float(qty or 0)
        r = float(rate or 0)
        # out of source godown, into destination godown
        stock.record_movement(s, item.id, 0.0, q, r, gfrom.id, v.id, v.date)
        stock.record_movement(s, item.id, q, 0.0, r, gto.id, v.id, v.date)
        s.commit()
        return number
    finally:
        s.close()