# services/reports.py
"""All financial & stock reports. Built on top of the voucher entries using
pandas for the grouping/aggregation.
"""
import pandas as pd
from db.engine import get_session
from db.models import Ledger, AccountGroup, VoucherEntry, Voucher
from core import stock


def _entries_df(s):
    rows = s.query(VoucherEntry.ledger_id, VoucherEntry.debit,
                   VoucherEntry.credit).all()
    if not rows:
        return pd.DataFrame(columns=["ledger_id", "debit", "credit"])
    return pd.DataFrame(rows, columns=["ledger_id", "debit", "credit"])


def _net_by_ledger(s):
    """Return dict ledger_id -> (debit_sum, credit_sum) including opening."""
    df = _entries_df(s)
    out = {}
    for l in s.query(Ledger).all():
        if df.empty:
            d = c = 0.0
        else:
            sub = df[df.ledger_id == l.id]
            d = float(sub["debit"].sum())
            c = float(sub["credit"].sum())
        ob = l.opening_balance or 0
        if (l.opening_dc or "Dr") == "Dr":
            d += ob
        else:
            c += ob
        out[l.id] = (round(d, 2), round(c, 2))
    return out


def trial_balance():
    s = get_session()
    try:
        nets = _net_by_ledger(s)
        names = {l.id: l.name for l in s.query(Ledger).all()}
        out, td, tc = [], 0.0, 0.0
        for lid, (d, c) in nets.items():
            net = round(d - c, 2)
            if net == 0:
                continue
            debit = net if net > 0 else 0
            credit = -net if net < 0 else 0
            td += debit
            tc += credit
            out.append({"Ledger": names[lid], "Debit": round(debit, 2),
                        "Credit": round(credit, 2)})
        out.append({"Ledger": "TOTAL", "Debit": round(td, 2),
                    "Credit": round(tc, 2)})
        return out
    finally:
        s.close()


def _nature_map(s):
    groups = {g.id: g.nature for g in s.query(AccountGroup).all()}
    return {l.id: (groups.get(l.group_id), l.name)
            for l in s.query(Ledger).all()}


def profit_and_loss():
    s = get_session()
    try:
        nets = _net_by_ledger(s)
        nat = _nature_map(s)
        income, expense, ti, te = [], [], 0.0, 0.0
        for lid, (d, c) in nets.items():
            nature, name = nat.get(lid, (None, "?"))
            if nature == "Income":
                amt = round(c - d, 2)
                if amt:
                    income.append({"Account": name, "Amount": amt})
                    ti += amt
            elif nature == "Expense":
                amt = round(d - c, 2)
                if amt:
                    expense.append({"Account": name, "Amount": amt})
                    te += amt
        rows = [{"Account": "--- INCOME ---", "Amount": ""}] + income
        rows += [{"Account": "Total Income", "Amount": round(ti, 2)}]
        rows += [{"Account": "--- EXPENSES ---", "Amount": ""}] + expense
        rows += [{"Account": "Total Expenses", "Amount": round(te, 2)}]
        rows += [{"Account": "NET PROFIT", "Amount": round(ti - te, 2)}]
        return rows
    finally:
        s.close()


def balance_sheet():
    s = get_session()
    try:
        nets = _net_by_ledger(s)
        nat = _nature_map(s)
        assets, liabs, ta, tl = [], [], 0.0, 0.0
        for lid, (d, c) in nets.items():
            nature, name = nat.get(lid, (None, "?"))
            if nature == "Asset":
                amt = round(d - c, 2)
                if amt:
                    assets.append({"Account": name, "Amount": amt})
                    ta += amt
            elif nature in ("Liability", "Capital"):
                amt = round(c - d, 2)
                if amt:
                    liabs.append({"Account": name, "Amount": amt})
                    tl += amt
        rows = [{"Account": "--- ASSETS ---", "Amount": ""}] + assets
        rows += [{"Account": "Total Assets", "Amount": round(ta, 2)}]
        rows += [{"Account": "--- LIABILITIES & CAPITAL ---", "Amount": ""}]
        rows += liabs
        rows += [{"Account": "Total Liabilities & Capital",
                  "Amount": round(tl, 2)}]
        return rows
    finally:
        s.close()


def gst_summary():
    s = get_session()
    try:
        df = _entries_df(s)
        want = ["CGST Output", "SGST Output", "IGST Output",
                "CGST Input", "SGST Input", "IGST Input"]
        out = []
        for l in s.query(Ledger).filter(Ledger.name.in_(want)).all():
            if df.empty:
                d = c = 0.0
            else:
                sub = df[df.ledger_id == l.id]
                d = float(sub["debit"].sum())
                c = float(sub["credit"].sum())
            amt = round((c - d) if "Output" in l.name else (d - c), 2)
            out.append({"Account": l.name, "Amount": amt})
        payable = sum(r["Amount"] for r in out if "Output" in r["Account"])
        credit = sum(r["Amount"] for r in out if "Input" in r["Account"])
        out.append({"Account": "NET GST PAYABLE",
                    "Amount": round(payable - credit, 2)})
        return out
    finally:
        s.close()


def day_book():
    s = get_session()
    try:
        vs = s.query(Voucher).order_by(Voucher.date.desc(),
                                       Voucher.id.desc()).all()
        return [{"Date": str(v.date), "Type": v.vtype, "Number": v.number,
                 "Party": v.party.name if v.party else "",
                 "Total": v.total, "Narration": v.narration or ""}
                for v in vs]
    finally:
        s.close()


def ledger_statement(ledger_name):
    s = get_session()
    try:
        l = s.query(Ledger).filter_by(name=ledger_name).one_or_none()
        if not l:
            return []
        rows = (s.query(VoucherEntry, Voucher)
                .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
                .filter(VoucherEntry.ledger_id == l.id)
                .order_by(Voucher.date, Voucher.id).all())
        bal = (l.opening_balance or 0) if (l.opening_dc or "Dr") == "Dr" \
            else -(l.opening_balance or 0)
        out = [{"Date": "Opening", "Voucher": "", "Debit": "", "Credit": "",
                "Balance": round(bal, 2)}]
        for e, v in rows:
            bal += (e.debit - e.credit)
            out.append({"Date": str(v.date),
                        "Voucher": f"{v.vtype} {v.number}",
                        "Debit": e.debit, "Credit": e.credit,
                        "Balance": round(bal, 2)})
        return out
    finally:
        s.close()


def stock_summary():
    from db.engine import get_session
    from db.models import Item
    from core import stock
    s = get_session()
    rows = []
    for it in s.query(Item).order_by(Item.name).all():
        qty = stock.current_qty(s, it.id)
        rate = stock.avg_cost(s, it.id) or (it.purchase_rate or 0)
        rows.append({
            "item": it.name,
            "name": it.name,
            "hsn": getattr(it, "hsn", "") or "",
            "qty": qty,
            "rate": rate,
            "value": round(qty * (rate or 0), 2),
        })
    return rows


def ledger_names():
    s = get_session()
    try:
        return [l.name for l in s.query(Ledger).order_by(Ledger.name).all()]
    finally:
        s.close()