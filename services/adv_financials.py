# services/adv_financials.py
"""Advanced financial analysis built on existing vouchers: monthly P&L trend,
cash flow by month, top customers and top-selling items.
"""
from db.engine import get_session
from db.models import (
    Ledger, AccountGroup, Voucher, VoucherEntry, VoucherItem, Item
)


def _nature_map(s):
    groups = {g.id: (g.nature or "") for g in s.query(AccountGroup).all()}
    return {l.id: groups.get(l.group_id, "")
            for l in s.query(Ledger).all()}


def monthly_pl(year):
    """Income, expense and profit for each month of a year."""
    year = str(year)
    s = get_session()
    try:
        nat = _nature_map(s)
        months = {f"{m:02d}": {"income": 0.0, "expense": 0.0}
                  for m in range(1, 13)}
        q = (s.query(VoucherEntry, Voucher)
             .join(Voucher, VoucherEntry.voucher_id == Voucher.id))
        for entry, v in q.all():
            if not v.date or v.date.strftime("%Y") != year:
                continue
            mm = v.date.strftime("%m")
            nature = nat.get(entry.ledger_id, "")
            if nature == "Income":
                months[mm]["income"] += (entry.credit or 0) - (entry.debit or 0)
            elif nature == "Expense":
                months[mm]["expense"] += (entry.debit or 0) - (entry.credit or 0)
        out = []
        for mm in sorted(months):
            inc = round(months[mm]["income"], 2)
            exp = round(months[mm]["expense"], 2)
            out.append({"Month": f"{year}-{mm}", "Income": inc,
                        "Expense": exp, "Profit": round(inc - exp, 2)})
        return out
    finally:
        s.close()


def cash_flow(year):
    """Monthly net movement across cash/bank ledgers (matched by name)."""
    year = str(year)
    s = get_session()
    try:
        cash_ids = {l.id for l in s.query(Ledger).all()
                    if "cash" in (l.name or "").lower()
                    or "bank" in (l.name or "").lower()}
        months = {f"{m:02d}": 0.0 for m in range(1, 13)}
        q = (s.query(VoucherEntry, Voucher)
             .join(Voucher, VoucherEntry.voucher_id == Voucher.id))
        for entry, v in q.all():
            if entry.ledger_id not in cash_ids:
                continue
            if not v.date or v.date.strftime("%Y") != year:
                continue
            mm = v.date.strftime("%m")
            months[mm] += (entry.debit or 0) - (entry.credit or 0)
        return [{"Month": f"{year}-{mm}",
                 "Net cash flow": round(months[mm], 2)}
                for mm in sorted(months)]
    finally:
        s.close()


def top_customers(limit=10):
    s = get_session()
    try:
        pmap = {l.id: l.name for l in s.query(Ledger).all()}
        totals = {}
        for v in s.query(Voucher).filter(Voucher.vtype == "Sales").all():
            totals[v.party_id] = totals.get(v.party_id, 0.0) + (v.total or 0)
        rows = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        return [{"Customer": pmap.get(pid, ""), "Sales": round(t, 2)}
                for pid, t in rows[:limit]]
    finally:
        s.close()


def top_items(limit=10):
    s = get_session()
    try:
        inames = {i.id: i.name for i in s.query(Item).all()}
        sales_ids = {v.id for v in s.query(Voucher)
                     .filter(Voucher.vtype == "Sales").all()}
        qty = {}
        val = {}
        for vi in s.query(VoucherItem).all():
            if vi.voucher_id not in sales_ids:
                continue
            qty[vi.item_id] = qty.get(vi.item_id, 0.0) + (vi.qty or 0)
            val[vi.item_id] = val.get(vi.item_id, 0.0) + (vi.amount or 0)
        rows = sorted(qty.items(), key=lambda x: x[1], reverse=True)
        return [{"Item": inames.get(iid, ""), "Qty sold": round(q, 2),
                 "Value": round(val.get(iid, 0), 2)}
                for iid, q in rows[:limit]]
    finally:
        s.close()