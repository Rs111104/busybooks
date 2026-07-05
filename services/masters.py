# services/masters.py
"""Create / list / update / delete master records
(groups, ledgers/parties, items, units). Returns plain dicts to the UI.
"""
from db.engine import get_session
from db.models import AccountGroup, Ledger, Item, Unit


# ==================== Account Groups ====================
def list_groups():
    s = get_session()
    try:
        return [{"id": g.id, "name": g.name, "nature": g.nature,
                 "parent_id": g.parent_id}
                for g in s.query(AccountGroup).order_by(AccountGroup.name).all()]
    finally:
        s.close()


def create_group(name, nature, parent_id=None):
    s = get_session()
    try:
        g = AccountGroup(name=name, nature=nature, parent_id=parent_id)
        s.add(g)
        s.commit()
        return g.id
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def update_group(group_id, name, nature):
    s = get_session()
    try:
        g = s.get(AccountGroup, group_id)
        if not g:
            raise ValueError("Group not found.")
        g.name = name
        g.nature = nature
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def delete_group(group_id):
    s = get_session()
    try:
        g = s.get(AccountGroup, group_id)
        if g:
            s.delete(g)
            s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# ==================== Ledgers / Parties ====================
def list_ledgers():
    s = get_session()
    try:
        rows = (s.query(Ledger, AccountGroup.name)
                .join(AccountGroup, Ledger.group_id == AccountGroup.id)
                .order_by(Ledger.name).all())
        return [{"id": l.id, "name": l.name, "group": gname,
                 "group_id": l.group_id,
                 "opening_balance": l.opening_balance,
                 "opening_dc": l.opening_dc, "is_party": l.is_party,
                 "gstin": l.gstin, "state": l.state, "phone": l.phone}
                for l, gname in rows]
    finally:
        s.close()


def create_ledger(name, group_id, opening_balance=0.0, opening_dc="Dr",
                  is_party=False, gstin=None, state=None, state_code=None,
                  address=None, phone=None, email=None, credit_limit=0.0):
    s = get_session()
    try:
        l = Ledger(name=name, group_id=group_id,
                   opening_balance=opening_balance, opening_dc=opening_dc,
                   is_party=is_party, gstin=gstin, state=state,
                   state_code=state_code, address=address, phone=phone,
                   email=email, credit_limit=credit_limit)
        s.add(l)
        s.commit()
        return l.id
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def update_ledger(ledger_id, name, group_id, opening_balance=0.0,
                  opening_dc="Dr", is_party=False, gstin=None, state=None,
                  state_code=None, address=None, phone=None, email=None,
                  credit_limit=0.0):
    s = get_session()
    try:
        l = s.get(Ledger, ledger_id)
        if not l:
            raise ValueError("Ledger not found.")
        l.name = name
        l.group_id = group_id
        l.opening_balance = opening_balance
        l.opening_dc = opening_dc
        l.is_party = is_party
        l.gstin = gstin
        l.state = state
        l.state_code = state_code
        l.address = address
        l.phone = phone
        l.email = email
        l.credit_limit = credit_limit
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def delete_ledger(ledger_id):
    s = get_session()
    try:
        l = s.get(Ledger, ledger_id)
        if l:
            s.delete(l)
            s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# ==================== Units ====================
def list_units():
    s = get_session()
    try:
        return [{"id": u.id, "name": u.name}
                for u in s.query(Unit).order_by(Unit.name).all()]
    finally:
        s.close()


def create_unit(name, decimals=2):
    s = get_session()
    try:
        u = Unit(name=name, decimals=decimals)
        s.add(u)
        s.commit()
        return u.id
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def update_unit(unit_id, name):
    s = get_session()
    try:
        u = s.get(Unit, unit_id)
        if not u:
            raise ValueError("Unit not found.")
        u.name = name
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def delete_unit(unit_id):
    s = get_session()
    try:
        u = s.get(Unit, unit_id)
        if u:
            s.delete(u)
            s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# ==================== Items ====================
def list_items():
    s = get_session()
    try:
        rows = s.query(Item).order_by(Item.name).all()
        units = {u.id: u.name for u in s.query(Unit).all()}
        return [{"id": it.id, "name": it.name, "hsn": it.hsn,
                 "gst_rate": it.gst_rate, "sale_rate": it.sale_rate,
                 "purchase_rate": it.purchase_rate,
                 "unit_id": it.unit_id,
                 "unit": units.get(it.unit_id, "")}
                for it in rows]
    finally:
        s.close()


def create_item(name, unit_id=None, hsn=None, gst_rate=0.0, sale_rate=0.0,
                purchase_rate=0.0, opening_qty=0.0, opening_rate=0.0,
                group_id=None):
    s = get_session()
    try:
        it = Item(name=name, unit_id=unit_id, hsn=hsn, gst_rate=gst_rate,
                  sale_rate=sale_rate, purchase_rate=purchase_rate,
                  opening_qty=opening_qty, opening_rate=opening_rate,
                  group_id=group_id)
        s.add(it)
        s.commit()
        return it.id
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def update_item(item_id, name, unit_id=None, hsn=None, gst_rate=0.0,
                sale_rate=0.0, purchase_rate=0.0):
    s = get_session()
    try:
        it = s.get(Item, item_id)
        if not it:
            raise ValueError("Item not found.")
        it.name = name
        it.unit_id = unit_id
        it.hsn = hsn
        it.gst_rate = gst_rate
        it.sale_rate = sale_rate
        it.purchase_rate = purchase_rate
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def delete_item(item_id):
    s = get_session()
    try:
        it = s.get(Item, item_id)
        if it:
            s.delete(it)
            s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()