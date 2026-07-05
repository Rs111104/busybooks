# ui/masters_screen.py
"""Master-data screens: Account Groups, Ledgers, Items, Units, Stock.

Each screen renders a styled grid plus a New/Edit/Delete/Refresh toolbar.
Reads/writes the ORM models directly for deterministic behaviour.
"""
import customtkinter as ctk

from ui import theme
from db.engine import get_session
from db.models import AccountGroup, Ledger, Item, Unit
from core import stock as stock_mod

NATURES = ["Assets", "Liabilities", "Income", "Expenses"]
DC = ["Dr", "Cr"]


# ---------------- shared UI helpers ----------------
def _render(app, title, headers, rows, on_new, on_edit, on_delete, on_refresh):
    app._clear()
    app._title(title)
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 8))
    theme.primary_button(bar, "+ New", on_new).pack(side="left", padx=4)
    theme.ghost_button(bar, "Edit", on_edit).pack(side="left", padx=4)
    theme.danger_button(bar, "Delete", on_delete).pack(side="left", padx=4)
    theme.ghost_button(bar, "Refresh", on_refresh).pack(side="left", padx=4)
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)
    from ui.app import _make_sheet
    app._cur_sheet = _make_sheet(holder, headers, rows)


def _current(app):
    from ui.app import _selected_row
    sheet = getattr(app, "_cur_sheet", None)
    if sheet is None:
        return None
    return _selected_row(sheet)


def _delete(app, model, refresh):
    row = _current(app)
    if not row:
        _toast(app, "Select a row first.")
        return
    s = get_session()
    obj = s.get(model, int(row[0]))
    if obj is not None:
        s.delete(obj)
        s.commit()
    refresh()


def _toast(parent, msg):
    top = ctk.CTkToplevel(parent)
    top.title("Notice")
    top.geometry("360x150")
    ctk.CTkLabel(top, text=msg, wraplength=320,
                 font=(theme.FONT, 13)).pack(padx=16, pady=16)
    theme.primary_button(top, "OK", top.destroy).pack(pady=8)
    try:
        top.grab_set()
    except Exception:
        pass


def _num(v, name):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        raise ValueError(name + " must be a number.")


class _Form(ctk.CTkToplevel):
    """Generic modal form. fields = list of dicts with keys:
    key, label, kind('text'|'option'|'check'), options(for option)."""

    def __init__(self, app, title, fields, values=None, on_save=None):
        super().__init__(app)
        self.title(title)
        self.geometry("440x560")
        self.on_save = on_save
        self.widgets = {}
        values = values or {}
        frm = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=16, pady=16)
        for f in fields:
            key = f["key"]
            ctk.CTkLabel(frm, text=f["label"], anchor="w",
                         font=(theme.FONT, 12, "bold")).pack(fill="x",
                                                             pady=(8, 2))
            kind = f.get("kind", "text")
            if kind == "option":
                opts = [str(o) for o in f["options"]]
                var = ctk.StringVar(value=str(values.get(key, opts[0])))
                ctk.CTkOptionMenu(frm, values=opts, variable=var).pack(
                    fill="x")
                self.widgets[key] = ("option", var)
            elif kind == "check":
                var = ctk.BooleanVar(value=bool(values.get(key, False)))
                ctk.CTkCheckBox(frm, text="Yes", variable=var).pack(
                    anchor="w")
                self.widgets[key] = ("check", var)
            else:
                e = ctk.CTkEntry(frm)
                v = values.get(key)
                if v is not None:
                    e.insert(0, str(v))
                e.pack(fill="x")
                self.widgets[key] = ("text", e)
        theme.primary_button(frm, "Save", self._save).pack(fill="x", pady=16)
        try:
            self.grab_set()
        except Exception:
            pass

    def _collect(self):
        out = {}
        for key, (kind, w) in self.widgets.items():
            out[key] = w.get().strip() if kind == "text" else w.get()
        return out

    def _save(self):
        data = self._collect()
        try:
            if self.on_save:
                self.on_save(data)
            self.destroy()
        except Exception as e:
            _toast(self, str(e))


def _group_name(s, gid):
    if not gid:
        return ""
    g = s.get(AccountGroup, gid)
    return g.name if g else ""


def _unit_name(s, uid):
    if not uid:
        return ""
    u = s.get(Unit, uid)
    return u.name if u else ""


# ---------------- Account Groups ----------------
def groups(app):
    def refresh():
        s = get_session()
        rows = [[g.id, g.name, g.nature or "", _group_name(s, g.parent_id)]
                for g in s.query(AccountGroup).order_by(
                    AccountGroup.name).all()]
        _render(app, "Account Groups",
                ["ID", "Name", "Nature", "Parent"], rows,
                new_g, edit_g, del_g, refresh)

    def _fields(s):
        parents = ["(none)"] + [g.name for g in
                                s.query(AccountGroup).order_by(
                                    AccountGroup.name).all()]
        return [
            {"key": "name", "label": "Name"},
            {"key": "nature", "label": "Nature", "kind": "option",
             "options": NATURES},
            {"key": "parent", "label": "Parent group", "kind": "option",
             "options": parents},
        ]

    def new_g():
        _Form(app, "New Group", _fields(get_session()),
              on_save=lambda d: _save_group(None, d, refresh))

    def edit_g():
        row = _current(app)
        if not row:
            _toast(app, "Select a row first.")
            return
        s = get_session()
        g = s.get(AccountGroup, int(row[0]))
        _Form(app, "Edit Group", _fields(s),
              values={"name": g.name, "nature": g.nature,
                      "parent": _group_name(s, g.parent_id) or "(none)"},
              on_save=lambda d: _save_group(g.id, d, refresh))

    def del_g():
        _delete(app, AccountGroup, refresh)
    refresh()


def _save_group(gid, d, refresh):
    if not d.get("name"):
        raise ValueError("Name is required.")
    s = get_session()
    parent_id = None
    if d.get("parent") and d["parent"] != "(none)":
        p = s.query(AccountGroup).filter_by(name=d["parent"]).first()
        parent_id = p.id if p else None
    if gid is None:
        s.add(AccountGroup(name=d["name"], nature=d.get("nature"),
                           parent_id=parent_id))
    else:
        g = s.get(AccountGroup, gid)
        g.name = d["name"]
        g.nature = d.get("nature")
        g.parent_id = parent_id
    s.commit()
    refresh()


# ---------------- Ledgers ----------------
def ledgers(app):
    def refresh():
        s = get_session()
        rows = [[l.id, l.name, _group_name(s, l.group_id),
                 l.opening_balance or 0, l.opening_dc or "Dr",
                 "Yes" if l.is_party else "No", l.gstin or ""]
                for l in s.query(Ledger).order_by(Ledger.name).all()]
        _render(app, "Ledgers",
                ["ID", "Name", "Group", "Opening", "Dr/Cr", "Party",
                 "GSTIN"], rows, new_l, edit_l, del_l, refresh)

    def _fields(s):
        groups_ = [g.name for g in s.query(AccountGroup).order_by(
            AccountGroup.name).all()] or ["(none)"]
        return [
            {"key": "name", "label": "Name"},
            {"key": "group", "label": "Group", "kind": "option",
             "options": groups_},
            {"key": "opening", "label": "Opening balance"},
            {"key": "dc", "label": "Dr / Cr", "kind": "option",
             "options": DC},
            {"key": "is_party", "label": "Is a party (customer/supplier)?",
             "kind": "check"},
            {"key": "gstin", "label": "GSTIN"},
            {"key": "state_code", "label": "State code"},
            {"key": "phone", "label": "Phone"},
            {"key": "email", "label": "Email"},
        ]

    def new_l():
        _Form(app, "New Ledger", _fields(get_session()),
              on_save=lambda d: _save_ledger(None, d, refresh))

    def edit_l():
        row = _current(app)
        if not row:
            _toast(app, "Select a row first.")
            return
        s = get_session()
        l = s.get(Ledger, int(row[0]))
        vals = {"name": l.name, "group": _group_name(s, l.group_id),
                "opening": l.opening_balance or 0, "dc": l.opening_dc or "Dr",
                "is_party": bool(l.is_party), "gstin": l.gstin or "",
                "state_code": l.state_code or "", "phone": l.phone or "",
                "email": l.email or ""}
        _Form(app, "Edit Ledger", _fields(s), values=vals,
              on_save=lambda d: _save_ledger(l.id, d, refresh))

    def del_l():
        _delete(app, Ledger, refresh)
    refresh()


def _save_ledger(lid, d, refresh):
    if not d.get("name"):
        raise ValueError("Name is required.")
    s = get_session()
    grp = s.query(AccountGroup).filter_by(name=d.get("group")).first()
    opening = _num(d.get("opening"), "Opening balance")
    l = Ledger(name=d["name"]) if lid is None else s.get(Ledger, lid)
    if lid is None:
        s.add(l)
    l.name = d["name"]
    l.group_id = grp.id if grp else None
    l.opening_balance = opening
    l.opening_dc = d.get("dc") or "Dr"
    l.is_party = bool(d.get("is_party"))
    l.gstin = d.get("gstin") or None
    l.state_code = d.get("state_code") or None
    l.phone = d.get("phone") or None
    l.email = d.get("email") or None
    s.commit()
    refresh()


# ---------------- Items ----------------
def items(app):
    def refresh():
        s = get_session()
        rows = [[i.id, i.name, i.hsn or "", i.gst_rate or 0,
                 i.sale_rate or 0, i.purchase_rate or 0,
                 _unit_name(s, i.unit_id)]
                for i in s.query(Item).order_by(Item.name).all()]
        _render(app, "Items",
                ["ID", "Name", "HSN", "GST%", "Sale", "Purchase", "Unit"],
                rows, new_i, edit_i, del_i, refresh)

    def _fields(s):
        units_ = [u.name for u in s.query(Unit).order_by(
            Unit.name).all()] or ["(none)"]
        return [
            {"key": "name", "label": "Name"},
            {"key": "hsn", "label": "HSN / SAC"},
            {"key": "gst_rate", "label": "GST %"},
            {"key": "sale_rate", "label": "Sale rate"},
            {"key": "purchase_rate", "label": "Purchase rate"},
            {"key": "unit", "label": "Unit", "kind": "option",
             "options": units_},
            {"key": "opening_qty", "label": "Opening qty"},
            {"key": "opening_rate", "label": "Opening rate"},
        ]

    def new_i():
        _Form(app, "New Item", _fields(get_session()),
              on_save=lambda d: _save_item(None, d, refresh))

    def edit_i():
        row = _current(app)
        if not row:
            _toast(app, "Select a row first.")
            return
        s = get_session()
        i = s.get(Item, int(row[0]))
        vals = {"name": i.name, "hsn": i.hsn or "",
                "gst_rate": i.gst_rate or 0, "sale_rate": i.sale_rate or 0,
                "purchase_rate": i.purchase_rate or 0,
                "unit": _unit_name(s, i.unit_id),
                "opening_qty": i.opening_qty or 0,
                "opening_rate": i.opening_rate or 0}
        _Form(app, "Edit Item", _fields(s), values=vals,
              on_save=lambda d: _save_item(i.id, d, refresh))

    def del_i():
        _delete(app, Item, refresh)
    refresh()


def _save_item(iid, d, refresh):
    if not d.get("name"):
        raise ValueError("Name is required.")
    s = get_session()
    unit = s.query(Unit).filter_by(name=d.get("unit")).first()
    i = Item(name=d["name"]) if iid is None else s.get(Item, iid)
    if iid is None:
        s.add(i)
    i.name = d["name"]
    i.hsn = d.get("hsn") or None
    i.gst_rate = _num(d.get("gst_rate"), "GST %")
    i.sale_rate = _num(d.get("sale_rate"), "Sale rate")
    i.purchase_rate = _num(d.get("purchase_rate"), "Purchase rate")
    i.unit_id = unit.id if unit else None
    i.opening_qty = _num(d.get("opening_qty"), "Opening qty")
    i.opening_rate = _num(d.get("opening_rate"), "Opening rate")
    s.commit()
    refresh()


# ---------------- Units ----------------
def units(app):
    def refresh():
        s = get_session()
        rows = [[u.id, u.name, u.decimals or 0]
                for u in s.query(Unit).order_by(Unit.name).all()]
        _render(app, "Units", ["ID", "Name", "Decimals"], rows,
                new_u, edit_u, del_u, refresh)

    def _fields():
        return [
            {"key": "name", "label": "Name (e.g. Nos, Kg, Ltr)"},
            {"key": "decimals", "label": "Decimals", "kind": "option",
             "options": [0, 1, 2, 3]},
        ]

    def new_u():
        _Form(app, "New Unit", _fields(),
              on_save=lambda d: _save_unit(None, d, refresh))

    def edit_u():
        row = _current(app)
        if not row:
            _toast(app, "Select a row first.")
            return
        s = get_session()
        u = s.get(Unit, int(row[0]))
        _Form(app, "Edit Unit", _fields(),
              values={"name": u.name, "decimals": u.decimals or 0},
              on_save=lambda d: _save_unit(u.id, d, refresh))

    def del_u():
        _delete(app, Unit, refresh)
    refresh()


def _save_unit(uid, d, refresh):
    if not d.get("name"):
        raise ValueError("Name is required.")
    s = get_session()
    try:
        dec = int(float(d.get("decimals") or 0))
    except (TypeError, ValueError):
        dec = 0
    if uid is None:
        s.add(Unit(name=d["name"], decimals=dec))
    else:
        u = s.get(Unit, uid)
        u.name = d["name"]
        u.decimals = dec
    s.commit()
    refresh()


# ---------------- Stock (read-only) ----------------
def stock(app):
    app._clear()
    app._title("Stock Summary")
    s = get_session()
    try:
        total = stock_mod.stock_value(s)
    except Exception:
        total = 0
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 8))
    theme.h2(bar, "Total stock value: Rs {:,.2f}".format(total)).pack(
        side="left", padx=4)
    theme.ghost_button(bar, "Refresh", lambda: stock(app)).pack(
        side="right", padx=4)
    try:
        rows = [[r["name"], r["qty"], r["rate"], r["value"]]
                for r in stock_mod.summary(s)]
    except Exception:
        rows = []
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)
    from ui.app import _make_sheet
    _make_sheet(holder, ["Item", "Qty", "Avg Cost", "Value"], rows)