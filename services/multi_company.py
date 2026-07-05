# services/multi_company.py -- read-only consolidation across companies
def companies():
    from db import engine as eng
    try:
        return list(eng.list_companies())
    except Exception:
        return []


def _totals_for_path(path):
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import Session
    from db.models import Voucher
    e = create_engine("sqlite:///" + path, future=True)
    sales = purchase = 0.0
    try:
        with Session(e) as s:
            sales = s.query(
                func.coalesce(func.sum(Voucher.total), 0.0)
            ).filter(Voucher.vtype == "Sales").scalar() or 0.0
            purchase = s.query(
                func.coalesce(func.sum(Voucher.total), 0.0)
            ).filter(Voucher.vtype == "Purchase").scalar() or 0.0
    except Exception:
        pass
    finally:
        e.dispose()
    return float(sales), float(purchase)


def consolidated():
    from db import engine as eng
    rows = []
    tot_s = tot_p = 0.0
    for slug in companies():
        try:
            path = eng.company_path(slug)
        except Exception:
            continue
        s, p = _totals_for_path(path)
        tot_s += s
        tot_p += p
        rows.append({"company": slug, "sales": round(s, 2),
                     "purchase": round(p, 2), "gross": round(s - p, 2)})
    rows.append({"company": "TOTAL", "sales": round(tot_s, 2),
                 "purchase": round(tot_p, 2),
                 "gross": round(tot_s - tot_p, 2)})
    return rows