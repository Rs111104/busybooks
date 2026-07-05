# services/currency.py
"""Multi-currency management: define currencies, exchange rates, convert."""
from db.engine import get_session
from db.models_currency import Currency
from utils.settings import get_setting, set_setting

_BASE_KEY = "base_currency"


def get_base():
    return get_setting(_BASE_KEY, "INR")


def set_base(code):
    code = (code or "").strip().upper()
    if not code:
        raise ValueError("Enter a base currency code.")
    set_setting(_BASE_KEY, code)


def list_currencies():
    s = get_session()
    try:
        return [{"id": c.id, "Code": c.code, "Name": c.name,
                 "Symbol": c.symbol, "Rate to base": c.rate_to_base}
                for c in s.query(Currency).order_by(Currency.code).all()]
    finally:
        s.close()


def add_currency(code, name, symbol, rate):
    code = (code or "").strip().upper()
    if not code:
        raise ValueError("Enter a currency code, e.g. USD.")
    s = get_session()
    try:
        c = s.query(Currency).filter_by(code=code).first()
        if c:
            c.name = name
            c.symbol = symbol
            c.rate_to_base = float(rate or 1)
        else:
            s.add(Currency(code=code, name=name, symbol=symbol,
                           rate_to_base=float(rate or 1)))
        s.commit()
    finally:
        s.close()


def set_rate(code, rate):
    s = get_session()
    try:
        c = s.query(Currency).filter_by(code=code.upper()).first()
        if not c:
            raise ValueError("Unknown currency.")
        c.rate_to_base = float(rate or 1)
        s.commit()
    finally:
        s.close()


def delete_currency(code):
    s = get_session()
    try:
        c = s.query(Currency).filter_by(code=code.upper()).first()
        if c:
            s.delete(c)
            s.commit()
    finally:
        s.close()


def _rate(s, code):
    code = (code or "").upper()
    if code == get_base().upper():
        return 1.0
    c = s.query(Currency).filter_by(code=code).first()
    if not c:
        raise ValueError(f"Currency {code} is not defined.")
    return c.rate_to_base or 1.0


def convert(amount, from_code, to_code):
    s = get_session()
    try:
        amount = float(amount or 0)
        base_amt = amount * _rate(s, from_code)        # into base
        return round(base_amt / _rate(s, to_code), 4)  # base into target
    finally:
        s.close()