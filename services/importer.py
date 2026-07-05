# services/importer.py
"""Bulk-import masters from Excel. Column headers are matched case-insensitively.
Items columns:   name, unit, hsn, gst, sale, purchase
Ledgers columns: name, group, opening, dc, party, gstin, state, state_code
"""
import pandas as pd
from services import masters


def _num(v):
    try:
        f = float(v)
        return 0.0 if f != f else f      # f != f is True only for NaN
    except Exception:
        return 0.0


def _text(row, key):
    if key not in row:
        return None
    val = row[key]
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None
    return s


def import_items(path):
    df = pd.read_excel(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    units = {u["name"].lower(): u["id"] for u in masters.list_units()}
    created, skipped = 0, 0
    for _, row in df.iterrows():
        name = _text(row, "name")
        if not name:
            continue
        unit_name = _text(row, "unit")
        uid = units.get(unit_name.lower()) if unit_name else None
        if unit_name and not uid:
            try:
                masters.create_unit(unit_name)
                units = {u["name"].lower(): u["id"]
                         for u in masters.list_units()}
                uid = units.get(unit_name.lower())
            except Exception:
                uid = None
        try:
            masters.create_item(name, unit_id=uid, hsn=_text(row, "hsn"),
                                gst_rate=_num(row.get("gst")),
                                sale_rate=_num(row.get("sale")),
                                purchase_rate=_num(row.get("purchase")))
            created += 1
        except Exception:
            skipped += 1
    return created, skipped


def import_ledgers(path):
    df = pd.read_excel(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    gmap = {g["name"].lower(): g["id"] for g in masters.list_groups()}
    created, skipped = 0, 0
    for _, row in df.iterrows():
        name = _text(row, "name")
        if not name:
            continue
        gname = _text(row, "group")
        gid = gmap.get(gname.lower()) if gname else None
        if not gid:
            skipped += 1
            continue
        party_txt = (_text(row, "party") or "").lower()
        try:
            masters.create_ledger(
                name, gid, opening_balance=_num(row.get("opening")),
                opening_dc=(_text(row, "dc") or "Dr"),
                is_party=party_txt in ("yes", "y", "true", "1"),
                gstin=_text(row, "gstin"), state=_text(row, "state"),
                state_code=_text(row, "state_code"))
            created += 1
        except Exception:
            skipped += 1
    return created, skipped