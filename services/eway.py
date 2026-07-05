# services/eway.py -- E-Way Bill JSON generator (portal schema)
import os
import json
from db.engine import get_session
from db.models import Voucher, Ledger, VoucherItem, Item, Company

_MODE = {"1": "Road", "2": "Rail", "3": "Air", "4": "Ship"}


def _company(s):
    return s.query(Company).first()


def sales_vouchers(limit=100):
    s = get_session()
    out = []
    for v in (s.query(Voucher).filter(Voucher.vtype == "Sales")
              .order_by(Voucher.id.desc()).limit(limit).all()):
        out.append({"id": v.id, "number": v.number or "",
                    "date": str(v.date), "total": round(v.total or 0, 2)})
    return out


def generate(voucher_id, distance_km=0, trans_mode="1", vehicle_no="",
             trans_doc_no="", trans_doc_date=""):
    """trans_mode: 1=Road 2=Rail 3=Air 4=Ship. Returns dict with path+json."""
    s = get_session()
    v = s.get(Voucher, voucher_id)
    if not v:
        return None
    co = _company(s)
    party = s.get(Ledger, v.party_id) if v.party_id else None
    items = []
    tot_val = tot_cgst = tot_sgst = tot_igst = 0.0
    for vi in (s.query(VoucherItem)
               .filter(VoucherItem.voucher_id == v.id).all()):
        it = s.get(Item, vi.item_id) if vi.item_id else None
        items.append({
            "productName": (it.name if it else ""),
            "hsnCode": (getattr(it, "hsn", "") or "") if it else "",
            "quantity": vi.qty or 0,
            "qtyUnit": "NOS",
            "taxableAmount": round(vi.amount or 0, 2),
            "cgstRate": (vi.gst_rate or 0) / 2 if (vi.cgst or 0) else 0,
            "sgstRate": (vi.gst_rate or 0) / 2 if (vi.sgst or 0) else 0,
            "igstRate": (vi.gst_rate or 0) if (vi.igst or 0) else 0,
        })
        tot_val += vi.amount or 0
        tot_cgst += vi.cgst or 0
        tot_sgst += vi.sgst or 0
        tot_igst += vi.igst or 0
    doc = {
        "version": "1.0.0421",
        "billLists": [{
            "supplyType": "O",
            "subSupplyType": "1",
            "docType": "INV",
            "docNo": v.number or str(v.id),
            "docDate": v.date.strftime("%d/%m/%Y") if v.date else "",
            "fromGstin": (co.gstin if co else "") or "",
            "fromPincode": 0,
            "fromStateCode": int((co.state_code if co else 0) or 0),
            "toGstin": (party.gstin if party else "") or "URP",
            "toPincode": 0,
            "toStateCode": int((getattr(party, "state_code", 0)
                                if party else 0) or 0),
            "totalValue": round(tot_val, 2),
            "cgstValue": round(tot_cgst, 2),
            "sgstValue": round(tot_sgst, 2),
            "igstValue": round(tot_igst, 2),
            "totInvValue": round(v.total or 0, 2),
            "transporterId": "",
            "transMode": str(trans_mode),
            "transDistance": str(distance_km),
            "vehicleNo": vehicle_no,
            "transDocNo": trans_doc_no,
            "transDocDate": trans_doc_date,
            "itemList": items,
        }],
    }
    outdir = os.path.join(os.getcwd(), "output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "eway_%s.json" % (v.number or v.id))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    return {"path": path, "json": doc,
            "mode": _MODE.get(str(trans_mode), "Road")}