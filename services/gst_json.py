# services/gst_json.py -- GSTR-1 JSON + B2B/B2C/HSN summaries
import json
import os
from datetime import datetime
from db.engine import get_session
from db.models import Voucher, VoucherItem, Item, Ledger, Company

SALES_TYPES = ("Sales",)


def _company(s):
    try:
        return s.query(Company).first()
    except Exception:
        return None


def _as_date(d):
    if isinstance(d, str):
        try:
            return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    return d


def _month_filter(vs, month, year):
    if not month and not year:
        return vs
    out = []
    for v in vs:
        d = _as_date(v.date)
        if not d:
            continue
        if year and d.year != year:
            continue
        if month and d.month != month:
            continue
        out.append(v)
    return out


def _lines(s, v):
    return s.query(VoucherItem).filter(
        VoucherItem.voucher_id == v.id).all()


def _fp(month, year):
    if month and year:
        return "%02d%04d" % (month, year)
    return ""


def gstr1(month=None, year=None):
    s = get_session()
    comp = _company(s)
    gstin = (comp.gstin if comp else "") or ""
    vs = s.query(Voucher).filter(Voucher.vtype.in_(SALES_TYPES)).all()
    vs = _month_filter(vs, month, year)

    b2b, b2cs, hsn = {}, {}, {}
    for v in vs:
        lines = _lines(s, v)
        taxable = round(sum((li.amount or 0) for li in lines), 2)
        cgst = round(sum((li.cgst or 0) for li in lines), 2)
        sgst = round(sum((li.sgst or 0) for li in lines), 2)
        igst = round(sum((li.igst or 0) for li in lines), 2)
        party = s.get(Ledger, v.party_id) if v.party_id else None
        pgstin = (party.gstin if party else "") or ""
        pos = (party.state_code if party else "") or ""
        if pgstin:
            b2b.setdefault(pgstin, []).append({
                "inum": v.number or "",
                "idt": str(v.date) if v.date else "",
                "val": round(v.total or (taxable + cgst + sgst + igst), 2),
                "pos": pos, "txval": taxable,
                "camt": cgst, "samt": sgst, "iamt": igst,
            })
        else:
            for li in lines:
                key = (li.gst_rate or 0, pos)
                a = b2cs.setdefault(key, {"txval": 0.0, "camt": 0.0,
                                          "samt": 0.0, "iamt": 0.0})
                a["txval"] += li.amount or 0
                a["camt"] += li.cgst or 0
                a["samt"] += li.sgst or 0
                a["iamt"] += li.igst or 0
        for li in lines:
            it = s.get(Item, li.item_id) if li.item_id else None
            code = (it.hsn if it else "") or "NA"
            a = hsn.setdefault(code, {"desc": (it.name if it else ""),
                                      "qty": 0.0, "txval": 0.0,
                                      "camt": 0.0, "samt": 0.0, "iamt": 0.0})
            a["qty"] += li.qty or 0
            a["txval"] += li.amount or 0
            a["camt"] += li.cgst or 0
            a["samt"] += li.sgst or 0
            a["iamt"] += li.igst or 0

    return {
        "gstin": gstin,
        "fp": _fp(month, year),
        "b2b": [{"ctin": g, "inv": inv} for g, inv in b2b.items()],
        "b2cs": [{"rt": k[0], "pos": k[1],
                  "txval": round(x["txval"], 2), "camt": round(x["camt"], 2),
                  "samt": round(x["samt"], 2), "iamt": round(x["iamt"], 2)}
                 for k, x in b2cs.items()],
        "hsn": [{"hsn_sc": c, "desc": x["desc"], "qty": round(x["qty"], 2),
                 "txval": round(x["txval"], 2), "camt": round(x["camt"], 2),
                 "samt": round(x["samt"], 2), "iamt": round(x["iamt"], 2)}
                for c, x in hsn.items()],
    }


def export_gstr1(path=None, month=None, year=None):
    doc = gstr1(month, year)
    if not path:
        base = os.path.join(os.getcwd(), "output")
        try:
            os.makedirs(base, exist_ok=True)
        except Exception:
            base = os.getcwd()
        suffix = ("_" + doc["fp"]) if doc.get("fp") else ""
        path = os.path.join(base, "GSTR1%s.json" % suffix)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    return path