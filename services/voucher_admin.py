# services/voucher_admin.py
"""List, view and delete saved vouchers. Deleting a voucher also removes its
ledger entries, item lines and stock movement (so stock is reversed).
"""
from db.engine import get_session
from db.models import (Voucher, VoucherEntry, VoucherItem, StockLedger,
                       Ledger, Item)


def list_vouchers(vtype=None, from_date=None, to_date=None):
    s = get_session()
    try:
        q = s.query(Voucher)
        if vtype and vtype != "All":
            q = q.filter(Voucher.vtype == vtype)
        if from_date:
            q = q.filter(Voucher.date >= from_date)
        if to_date:
            q = q.filter(Voucher.date <= to_date)
        vs = q.order_by(Voucher.date.desc(), Voucher.id.desc()).all()
        return [{"id": v.id, "date": str(v.date), "vtype": v.vtype,
                 "number": v.number,
                 "party": v.party.name if v.party else "",
                 "total": v.total, "narration": v.narration or ""}
                for v in vs]
    finally:
        s.close()


def get_voucher(vid):
    s = get_session()
    try:
        v = s.get(Voucher, vid)
        if not v:
            return None
        lnames = {l.id: l.name for l in s.query(Ledger).all()}
        inames = {i.id: i.name for i in s.query(Item).all()}
        entries = [{"ledger": lnames.get(e.ledger_id, e.ledger_id),
                    "debit": e.debit, "credit": e.credit}
                   for e in v.entries]
        items = [{"item": inames.get(it.item_id, it.item_id), "qty": it.qty,
                  "rate": it.rate, "amount": it.amount,
                  "gst_rate": it.gst_rate} for it in v.items]
        return {"id": v.id, "date": str(v.date), "vtype": v.vtype,
                "number": v.number,
                "party": v.party.name if v.party else "",
                "total": v.total, "narration": v.narration or "",
                "entries": entries, "items": items}
    finally:
        s.close()


def delete_voucher(vid):
    s = get_session()
    try:
        v = s.get(Voucher, vid)
        if not v:
            raise ValueError("Voucher not found.")
        s.query(StockLedger).filter(StockLedger.voucher_id == vid).delete()
        s.query(VoucherItem).filter(VoucherItem.voucher_id == vid).delete()
        s.query(VoucherEntry).filter(VoucherEntry.voucher_id == vid).delete()
        s.delete(v)
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()