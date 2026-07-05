# services/datatools.py
"""Backup/restore, master export, and year-end closing balances."""
import os
import shutil
from datetime import datetime

from db.engine import get_session
from db.models import Ledger, Item, Voucher, VoucherEntry
from output import export

BACKUP_DIR = "backups"
COMPANIES_DIR = "companies"


def _ensure(d):
    os.makedirs(d, exist_ok=True)


def backup_all():
    """Zip the whole companies/ folder into backups/backup_<stamp>.zip."""
    _ensure(BACKUP_DIR)
    _ensure(COMPANIES_DIR)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(BACKUP_DIR, f"backup_{stamp}")
    return shutil.make_archive(base, "zip", COMPANIES_DIR)


def list_backups():
    _ensure(BACKUP_DIR)
    return sorted([f for f in os.listdir(BACKUP_DIR)
                   if f.lower().endswith(".zip")], reverse=True)


def restore_backup(name):
    _ensure(COMPANIES_DIR)
    path = os.path.join(BACKUP_DIR, name)
    if not os.path.exists(path):
        raise ValueError("Backup file not found.")
    shutil.unpack_archive(path, COMPANIES_DIR, "zip")
    return True


def export_masters():
    _ensure("exports")
    s = get_session()
    try:
        out = []
        lheaders = ["Name", "GSTIN", "Phone", "Email", "Opening", "Dr/Cr"]
        lrows = [[l.name, l.gstin or "", l.phone or "", l.email or "",
                  l.opening_balance or 0, l.opening_dc or "Dr"]
                 for l in s.query(Ledger).order_by(Ledger.name).all()]
        out.append(export.rows_to_excel("ledgers", lheaders, lrows))
        iheaders = ["Name", "HSN", "GST%", "Sale rate", "Purchase rate"]
        irows = [[i.name, i.hsn or "", i.gst_rate or 0, i.sale_rate or 0,
                  i.purchase_rate or 0]
                 for i in s.query(Item).order_by(Item.name).all()]
        out.append(export.rows_to_excel("items", iheaders, irows))
        return out
    finally:
        s.close()


def _ledger_balance(s, led, upto_year=None):
    bal = led.opening_balance or 0
    if (led.opening_dc or "Dr") == "Cr":
        bal = -bal
    q = (s.query(VoucherEntry, Voucher)
         .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
         .filter(VoucherEntry.ledger_id == led.id))
    for entry, v in q.all():
        if upto_year and v.date and v.date.strftime("%Y") > str(upto_year):
            continue
        bal += (entry.debit or 0) - (entry.credit or 0)
    return bal


def closing_balances(year):
    """Opening + movement per ledger up to the end of a year."""
    s = get_session()
    try:
        result = []
        for led in s.query(Ledger).order_by(Ledger.name).all():
            bal = _ledger_balance(s, led, year)
            result.append({"Ledger": led.name,
                           "Closing balance": round(abs(bal), 2),
                           "Dr/Cr": "Dr" if bal >= 0 else "Cr"})
        return result
    finally:
        s.close()


def carry_forward():
    """Set each ledger's opening balance to its current closing balance.
    Use at the start of a new financial year. Changes opening balances.
    """
    s = get_session()
    try:
        for led in s.query(Ledger).all():
            bal = _ledger_balance(s, led)
            led.opening_balance = round(abs(bal), 2)
            led.opening_dc = "Dr" if bal >= 0 else "Cr"
        s.commit()
    finally:
        s.close()