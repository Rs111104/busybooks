# services/pricing.py
"""Pricing: named price lists with quantity tiers, discount schemes, and
party-specific price-list assignment.
"""
import json

from db.engine import get_session
from db.models import Item
from db.models_pricing import PriceList, PriceListItem
from utils.settings import get_setting, set_setting

_SCHEMES_KEY = "discount_schemes"
_PARTY_KEY = "party_pricelist"


def item_names():
    s = get_session()
    try:
        return [i.name for i in s.query(Item).order_by(Item.name).all()]
    finally:
        s.close()


# ---------- price lists ----------
def create_price_list(name):
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a price list name.")
    s = get_session()
    try:
        if s.query(PriceList).filter_by(name=name).first():
            raise ValueError("That price list already exists.")
        s.add(PriceList(name=name))
        s.commit()
    finally:
        s.close()


def list_price_lists():
    s = get_session()
    try:
        return [pl.name for pl in s.query(PriceList).order_by(PriceList.name).all()]
    finally:
        s.close()


def set_price(list_name, item_name, rate, min_qty=1.0):
    s = get_session()
    try:
        pl = s.query(PriceList).filter_by(name=list_name).first()
        if not pl:
            raise ValueError("Unknown price list.")
        item = s.query(Item).filter_by(name=item_name).first()
        if not item:
            raise ValueError("Unknown item.")
        mq = float(min_qty or 1)
        row = (s.query(PriceListItem)
               .filter_by(price_list_id=pl.id, item_id=item.id, min_qty=mq)
               .first())
        if row:
            row.rate = float(rate or 0)
        else:
            s.add(PriceListItem(price_list_id=pl.id, item_id=item.id,
                               min_qty=mq, rate=float(rate or 0)))
        s.commit()
    finally:
        s.close()


def list_prices(list_name):
    s = get_session()
    try:
        pl = s.query(PriceList).filter_by(name=list_name).first()
        if not pl:
            return []
        inames = {i.id: i.name for i in s.query(Item).all()}
        rows = (s.query(PriceListItem).filter_by(price_list_id=pl.id)
                .order_by(PriceListItem.item_id, PriceListItem.min_qty).all())
        return [{"Item": inames.get(r.item_id, "?"), "Min qty": r.min_qty,
                 "Rate": r.rate} for r in rows]
    finally:
        s.close()


def price_for(item_name, qty=1, list_name=None):
    """Best tier rate for item+qty in a list; falls back to item sale rate."""
    qty = float(qty or 1)
    s = get_session()
    try:
        item = s.query(Item).filter_by(name=item_name).first()
        if not item:
            raise ValueError("Unknown item.")
        best = None
        if list_name:
            pl = s.query(PriceList).filter_by(name=list_name).first()
            if pl:
                rows = (s.query(PriceListItem)
                        .filter_by(price_list_id=pl.id, item_id=item.id)
                        .filter(PriceListItem.min_qty <= qty)
                        .order_by(PriceListItem.min_qty.desc()).all())
                if rows:
                    best = rows[0].rate
        if best is None:
            best = item.sale_rate or 0.0
        return best
    finally:
        s.close()


# ---------- discount schemes (stored in Settings as JSON) ----------
def _load_schemes():
    raw = get_setting(_SCHEMES_KEY, "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def _save_schemes(schemes):
    set_setting(_SCHEMES_KEY, json.dumps(schemes))


def list_schemes():
    return _load_schemes()


def add_scheme(name, dtype, value, min_amount=0.0):
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a scheme name.")
    if dtype not in ("percent", "flat"):
        raise ValueError("Type must be 'percent' or 'flat'.")
    schemes = _load_schemes()
    schemes = [x for x in schemes if x.get("name") != name]
    schemes.append({"name": name, "type": dtype, "value": float(value or 0),
                    "min_amount": float(min_amount or 0)})
    _save_schemes(schemes)


def remove_scheme(name):
    schemes = [x for x in _load_schemes() if x.get("name") != name]
    _save_schemes(schemes)


def best_discount(amount):
    """Return (scheme_name, discount_value) giving the biggest discount for a
    given bill amount, or (None, 0.0).
    """
    amount = float(amount or 0)
    best_name, best_disc = None, 0.0
    for sc in _load_schemes():
        if amount < sc.get("min_amount", 0):
            continue
        if sc["type"] == "percent":
            disc = amount * sc["value"] / 100.0
        else:
            disc = sc["value"]
        if disc > best_disc:
            best_name, best_disc = sc["name"], disc
    return best_name, round(best_disc, 2)


# ---------- party -> price list link ----------
def _load_party_map():
    raw = get_setting(_PARTY_KEY, "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def set_party_pricelist(party_name, list_name):
    m = _load_party_map()
    if list_name:
        m[party_name] = list_name
    else:
        m.pop(party_name, None)
    set_setting(_PARTY_KEY, json.dumps(m))


def get_party_pricelist(party_name):
    return _load_party_map().get(party_name)