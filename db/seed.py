# db/seed.py
"""Seed default masters into a fresh company database."""
from datetime import date
from db.engine import get_session
from db.models import (
    Company, AccountGroup, Ledger, Unit, NumberSeries
)

# (name, parent_name or None, nature, is_primary)
DEFAULT_GROUPS = [
    ("Capital Account", None, "Capital", True),
    ("Loans (Liability)", None, "Liability", True),
    ("Current Liabilities", None, "Liability", True),
    ("Duties & Taxes", "Current Liabilities", "Liability", False),
    ("Sundry Creditors", "Current Liabilities", "Liability", False),
    ("Fixed Assets", None, "Asset", True),
    ("Investments", None, "Asset", True),
    ("Current Assets", None, "Asset", True),
    ("Bank Accounts", "Current Assets", "Asset", False),
    ("Cash-in-hand", "Current Assets", "Asset", False),
    ("Sundry Debtors", "Current Assets", "Asset", False),
    ("Stock-in-hand", "Current Assets", "Asset", False),
    ("Sales Accounts", None, "Income", True),
    ("Purchase Accounts", None, "Expense", True),
    ("Direct Expenses", None, "Expense", True),
    ("Indirect Expenses", None, "Expense", True),
    ("Direct Incomes", None, "Income", True),
    ("Indirect Incomes", None, "Income", True),
]

DEFAULT_UNITS = ["Nos", "Kg", "Ltr", "Mtr", "Box", "Pcs"]

DEFAULT_SERIES = [
    ("Sales", "INV/"), ("Purchase", "PUR/"), ("Payment", "PAY/"),
    ("Receipt", "REC/"), ("Contra", "CON/"), ("Journal", "JV/"),
    ("CreditNote", "CN/"), ("DebitNote", "DN/"), ("StockJournal", "SJ/"),
]


def seed_company(name: str, state: str = "", state_code: str = "",
                 gstin: str = ""):
    s = get_session()
    if s.query(Company).count() == 0:
        s.add(Company(name=name, state=state, state_code=state_code,
                      gstin=gstin))

    # account groups (two passes so parents exist before children)
    if s.query(AccountGroup).count() == 0:
        by_name = {}
        for gname, parent, nature, primary in DEFAULT_GROUPS:
            g = AccountGroup(name=gname, nature=nature, is_primary=primary)
            s.add(g)
            s.flush()
            by_name[gname] = g
        for gname, parent, nature, primary in DEFAULT_GROUPS:
            if parent:
                by_name[gname].parent_id = by_name[parent].id

        # default ledgers
        s.add(Ledger(name="Cash", group_id=by_name["Cash-in-hand"].id))
        s.add(Ledger(name="Profit & Loss A/c",
                     group_id=by_name["Capital Account"].id))
        s.add(Ledger(name="Sales", group_id=by_name["Sales Accounts"].id))
        s.add(Ledger(name="Purchase",
                     group_id=by_name["Purchase Accounts"].id))
        s.add(Ledger(name="CGST Output",
                     group_id=by_name["Duties & Taxes"].id))
        s.add(Ledger(name="SGST Output",
                     group_id=by_name["Duties & Taxes"].id))
        s.add(Ledger(name="IGST Output",
                     group_id=by_name["Duties & Taxes"].id))
        s.add(Ledger(name="CGST Input",
                     group_id=by_name["Duties & Taxes"].id))
        s.add(Ledger(name="SGST Input",
                     group_id=by_name["Duties & Taxes"].id))
        s.add(Ledger(name="IGST Input",
                     group_id=by_name["Duties & Taxes"].id))

    if s.query(Unit).count() == 0:
        for u in DEFAULT_UNITS:
            s.add(Unit(name=u))

    if s.query(NumberSeries).count() == 0:
        for vtype, prefix in DEFAULT_SERIES:
            s.add(NumberSeries(vtype=vtype, prefix=prefix, next_no=1))

    s.commit()
    s.close()