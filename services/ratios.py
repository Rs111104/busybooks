# services/ratios.py -- key business figures & ratios
from db.engine import get_session
from db.models import Voucher


def _sum(vtype):
    s = get_session()
    return sum((v.total or 0)
               for v in s.query(Voucher).filter(Voucher.vtype == vtype).all())


def ratios():
    sales = _sum("Sales")
    purch = _sum("Purchase")
    gp = sales - purch
    gpm = (gp / sales * 100) if sales else 0
    recv = pay = 0
    try:
        from services import analytics
        recv, pay = analytics.receivables_payables()
    except Exception:
        pass
    rp = (recv / pay) if pay else 0
    return [
        ("Total Sales", round(sales, 2)),
        ("Total Purchases", round(purch, 2)),
        ("Gross Profit (Sales - Purchases)", round(gp, 2)),
        ("Gross Profit Margin %", round(gpm, 2)),
        ("Receivables", round(recv, 2)),
        ("Payables", round(pay, 2)),
        ("Receivable / Payable Ratio", round(rp, 2)),
    ]