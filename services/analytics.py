# services/analytics.py
"""Numbers for the analytics dashboard: sales trend, top items, AR vs AP."""
from db.engine import get_session
from db.models import (
    Ledger, AccountGroup, Voucher, VoucherEntry, VoucherItem, Item
)


def sales_by_month(year):
    year = str(year)
    s = get_session()
    try:
        months = {f"{m:02d}": 0.0 for m in range(1, 13)}
        for v in s.query(Voucher).filter(Voucher.vtype == "Sales").all():
            if v.date and v.date.strftime("%Y") == year:
                months[v.date.strftime("%m")] += (v.total or 0)
        labels = [str(int(m)) for m in sorted(months)]
        values = [round(months[m], 2) for m in sorted(months)]
        return labels, values
    finally:
        s.close()


def top_items(limit=8):
    s = get_session()
    try:
        inames = {i.id: i.name for i in s.query(Item).all()}
        sales_ids = {v.id for v in s.query(Voucher)
                     .filter(Voucher.vtype == "Sales").all()}
        val = {}
        for vi in s.query(VoucherItem).all():
            if vi.voucher_id in sales_ids:
                val[vi.item_id] = val.get(vi.item_id, 0.0) + (vi.amount or 0)
        rows = sorted(val.items(), key=lambda x: x[1], reverse=True)[:limit]
        return ([inames.get(i, "?") for i, _ in rows],
                [round(v, 2) for _, v in rows])
    finally:
        s.close()


def receivables_payables():
    s = get_session()
    try:
        gname = {g.id: (g.name or "") for g in s.query(AccountGroup).all()}
        recv = 0.0
        pay = 0.0
        for led in s.query(Ledger).all():
            bal = led.opening_balance or 0
            if (led.opening_dc or "Dr") == "Cr":
                bal = -bal
            for e in s.query(VoucherEntry).filter_by(ledger_id=led.id).all():
                bal += (e.debit or 0) - (e.credit or 0)
            name = gname.get(led.group_id, "").lower()
            if "debtor" in name:
                recv += bal
            elif "creditor" in name:
                pay += -bal
        return round(recv, 2), round(pay, 2)
    finally:
        s.close()