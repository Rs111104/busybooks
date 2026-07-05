# services/multi_company.py -- consolidated results across companies
from sqlalchemy import create_engine, text
from db import engine as eng


def companies():
    try:
        return eng.list_companies()
    except Exception:
        return []


def _sums(path):
    e = create_engine("sqlite:///" + path, future=True)
    sales = purch = 0.0
    try:
        with e.connect() as c:
            sales = c.execute(text(
                "SELECT COALESCE(SUM(total),0) FROM voucher "
                "WHERE vtype='Sales'")).scalar() or 0
            purch = c.execute(text(
                "SELECT COALESCE(SUM(total),0) FROM voucher "
                "WHERE vtype='Purchase'")).scalar() or 0
    except Exception:
        pass
    finally:
        e.dispose()
    return float(sales), float(purch)


def consolidated():
    out = []
    for slug in companies():
        try:
            path = eng.company_path(slug)
        except Exception:
            continue
        sales, purch = _sums(path)
        out.append({"company": slug, "sales": round(sales, 2),
                    "purchase": round(purch, 2),
                    "gross": round(sales - purch, 2)})
    return out