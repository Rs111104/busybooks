# services/pos.py
"""Point of Sale: fast retail billing that reuses the sales invoice engine."""
from db.engine import get_session
from db.models import Item, Ledger, AccountGroup
from services import trading


def item_list():
    s = get_session()
    try:
        return [{"id": i.id, "name": i.name, "rate": i.sale_rate or 0,
                 "gst_rate": i.gst_rate or 0}
                for i in s.query(Item).order_by(Item.name).all()]
    finally:
        s.close()


def party_list():
    s = get_session()
    try:
        return [l.name for l in s.query(Ledger)
                .filter(Ledger.is_party == True)  # noqa: E712
                .order_by(Ledger.name).all()]
    finally:
        s.close()


def ensure_walkin():
    """Find or create a 'Walk-in Customer' party ledger."""
    s = get_session()
    try:
        led = s.query(Ledger).filter_by(name="Walk-in Customer").first()
        if led:
            return led.id
        grp = (s.query(AccountGroup)
               .filter(AccountGroup.name.in_(["Sundry Debtors",
                                              "Debtors"])).first())
        led = Ledger(name="Walk-in Customer",
                     group_id=grp.id if grp else None,
                     is_party=True, opening_balance=0, opening_dc="Dr")
        s.add(led)
        s.commit()
        return led.id
    finally:
        s.close()


def _party_id(name):
    s = get_session()
    try:
        led = s.query(Ledger).filter_by(name=name).first()
        return led.id if led else None
    finally:
        s.close()


def checkout(cart, party_name=None):
    """cart = list of {item_id, qty, rate, gst_rate}. Returns invoice number.
    """
    if not cart:
        raise ValueError("Cart is empty.")
    if party_name and party_name not in ("Walk-in Customer", "", None):
        pid = _party_id(party_name)
    else:
        pid = ensure_walkin()
    if not pid:
        raise ValueError("Could not resolve the customer.")
    lines = [{"item_id": c["item_id"], "qty": float(c["qty"]),
              "rate": float(c["rate"]),
              "gst_rate": float(c.get("gst_rate", 0))}
             for c in cart]
    v = trading.create_sales_invoice(pid, lines, narration="POS sale")
    num = getattr(v, "number", None)
    return num or str(v)