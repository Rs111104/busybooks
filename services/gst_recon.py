# services/gst_recon.py -- match 2A/2B portal JSON vs purchase books
import json
from db.engine import get_session
from db.models import Voucher, Ledger


def _our_purchases():
    s = get_session()
    out = []
    for v in s.query(Voucher).filter(Voucher.vtype == "Purchase").all():
        party = s.get(Ledger, v.party_id) if v.party_id else None
        out.append({"gstin": (party.gstin if party else "") or "",
                    "inum": v.number or "",
                    "val": round(v.total or 0, 2)})
    return out


def _portal(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else (
        data.get("b2b") or data.get("docdata") or [])
    out = []
    for r in items:
        out.append({"gstin": r.get("ctin") or r.get("gstin") or "",
                    "inum": r.get("inum") or r.get("inv_no") or "",
                    "val": float(r.get("val") or r.get("value") or 0)})
    return out


def reconcile(portal_json_path):
    portal = _portal(portal_json_path)
    ours = _our_purchases()
    idx = {(o["gstin"], o["inum"]): o for o in ours}
    seen = set()
    result = []
    for p in portal:
        k = (p["gstin"], p["inum"])
        seen.add(k)
        if k in idx:
            diff = round(idx[k]["val"] - p["val"], 2)
            status = "Matched" if abs(diff) < 1 else "Value mismatch"
            result.append({"gstin": p["gstin"], "inum": p["inum"],
                           "portal": p["val"], "books": idx[k]["val"],
                           "status": status})
        else:
            result.append({"gstin": p["gstin"], "inum": p["inum"],
                           "portal": p["val"], "books": 0.0,
                           "status": "Missing in books"})
    for o in ours:
        if (o["gstin"], o["inum"]) not in seen:
            result.append({"gstin": o["gstin"], "inum": o["inum"],
                           "portal": 0.0, "books": o["val"],
                           "status": "Missing in 2A/2B"})
    return result