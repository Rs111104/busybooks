# ui/app.py
"""BusyBooks main window: a modern, Busy-style desktop shell.

Keeps the public surface other screens rely on:
  App.content, App._clear, App._title, App._open,
  App.show_dashboard/show_groups/show_ledgers/show_items/show_units/show_stock,
  module-level _make_sheet, _selected_row, and run().
"""
import importlib
import pkgutil
import datetime

import customtkinter as ctk

import ui
from ui import theme
from db.engine import get_session
from db.models import AccountGroup, Ledger, Item, Unit, Voucher
from core import stock as stock_mod

try:
    from utils.settings import get_setting
    COMPANY = get_setting("company", "Demo Traders")
except Exception:
    COMPANY = "Demo Traders"

APP_TITLE = "BusyBooks - Accounting & Inventory"

# Curated menu. Each item: (label, kind, target)
#   kind "m" -> App method name; kind "s" -> (module, function)
# Any screen file not listed here is auto-added under "More".
NAV = [
    ("Masters", [
        ("Account Groups", "m", "show_groups"),
        ("Ledgers", "m", "show_ledgers"),
        ("Items", "m", "show_items"),
        ("Units", "m", "show_units"),
    ]),
    ("Transactions", [
        ("Vouchers", "s", ("ui.vouchers_screen", "show_vouchers")),
        ("Point of Sale", "s", ("ui.pos_screen", "show_pos")),
        ("Orders & Quotations", "s", ("ui.orders_screen", "show_orders")),
        ("Manufacturing", "s", ("ui.manufacturing_screen", "show_manufacturing")),
        ("Pricing & Discounts", "s", ("ui.pricing_screen", "show_pricing")),
    ]),
    ("Inventory", [
        ("Stock Summary", "m", "show_stock"),
        ("Advanced Inventory", "s", ("ui.inventory_adv_screen", "show_inventory_adv")),
        ("Item Ledger", "s", ("ui.item_ledger_screen", "show_item_ledger")),
    ]),
    ("Reports", [
        ("Financial Reports", "s", ("ui.reports_screen", "show_reports")),
        ("Advanced Financials", "s", ("ui.adv_financials_screen", "show_adv_financials")),
        ("Outstanding", "s", ("ui.outstanding_screen", "show_outstanding")),
        ("Registers", "s", ("ui.registers_screen", "show_registers")),
        ("Cash Book", "s", ("ui.cashbook_screen", "show_cashbook")),
        ("Ratios", "s", ("ui.ratios_screen", "show_ratios")),
        ("Analytics Dashboard", "s", ("ui.analytics_screen", "show_analytics")),
        ("Reminders", "s", ("ui.reminders_screen", "show_reminders")),
    ]),
    ("GST & Tax", [
        ("GST Returns", "s", ("ui.gst_returns_screen", "show_gst_returns")),
        ("TDS / TCS", "s", ("ui.taxes_screen", "show_taxes")),
        ("E-Invoice", "s", ("ui.einvoice_screen", "show_einvoice")),
        ("Cost Centres & Budgets", "s", ("ui.costing_screen", "show_costing")),
    ]),
    ("Banking", [
        ("Banking Suite", "s", ("ui.banking_screen", "show_banking")),
        ("Bank Reconciliation", "s", ("ui.bank_screen", "show_bank")),
        ("Import Data", "s", ("ui.importer_screen", "show_importer")),
    ]),
    ("Tools", [
        ("Multi-currency", "s", ("ui.currency_screen", "show_currency")),
        ("Template Designer", "s", ("ui.designer_screen", "show_designer")),
        ("Communication", "s", ("ui.comms_screen", "show_comms")),
        ("Data & Year-end", "s", ("ui.datatools_screen", "show_datatools")),
    ]),
    ("Admin", [
        ("Users & Security", "s", ("ui.security_screen", "show_security")),
        ("Backup & Users", "s", ("ui.admin_screen", "show_admin")),
    ]),
]


# ---------- module-level helpers (used by many screens) ----------
def _make_sheet(parent, headers, data):
    from tksheet import Sheet
    sheet = Sheet(parent, headers=list(headers),
                  data=[list(r) for r in data])
    try:
        sheet.enable_bindings()
    except Exception:
        try:
            sheet.enable_bindings("all")
        except Exception:
            pass
    theme.style_sheet(sheet)
    sheet.pack(fill="both", expand=True)
    return sheet


def _selected_row(sheet):
    try:
        sel = sheet.get_currently_selected()
        row = None
        if sel is None:
            try:
                rows = sheet.get_selected_rows()
                if rows:
                    row = sorted(rows)[0]
            except Exception:
                row = None
        else:
            row = getattr(sel, "row", None)
            if row is None and isinstance(sel, (tuple, list)) and sel:
                row = sel[0]
        if row is None:
            return None
        return sheet.get_row_data(row)
    except Exception:
        return None


def _money(x):
    try:
        return "Rs " + format(float(x), ",.2f")
    except Exception:
        return str(x)


def _screen_exists(module, func):
    try:
        m = importlib.import_module(module)
    except Exception:
        return False
    return callable(getattr(m, func, None))


def _label_from(module_name):
    base = module_name[:-7] if module_name.endswith("_screen") else module_name
    return base.replace("_", " ").title()


def _discover_screens():
    out = []
    try:
        for mod in pkgutil.iter_modules(ui.__path__):
            name = mod.name
            if not name.endswith("_screen") or name == "masters_screen":
                continue
            module = "ui." + name
            try:
                m = importlib.import_module(module)
            except Exception:
                continue
            for attr in dir(m):
                if attr.startswith("show_") and callable(getattr(m, attr)):
                    out.append((module, attr, _label_from(name)))
                    break
    except Exception:
        pass
    return out


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x740")
        self.minsize(1000, 640)

        self._nav_buttons = []
        self._sections = []
        self._active_btn = None
        self._mode = "light"
        self._search_var = ctk.StringVar()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_body()
        self._build_statusbar()
        self._bind_shortcuts()

        self.show_dashboard()

    # ---------- top bar ----------
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, height=54, corner_radius=0,
                           fg_color=theme.PRIMARY)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        ctk.CTkLabel(bar, text="BusyBooks", text_color="white",
                     font=(theme.FONT, 18, "bold")).pack(side="left",
                                                         padx=(16, 8))
        ctk.CTkLabel(bar, text="|  " + COMPANY, text_color="#cfe0ee",
                     font=(theme.FONT, 13)).pack(side="left")
        ctk.CTkLabel(bar, text=datetime.date.today().strftime("%d %b %Y"),
                     text_color="#cfe0ee",
                     font=(theme.FONT, 12)).pack(side="right", padx=16)
        ctk.CTkButton(bar, text="Theme", width=76, height=30,
                      fg_color=theme.PRIMARY_DARK, hover_color="#0f3f61",
                      command=self._toggle_mode).pack(side="right", padx=8)

    def _toggle_mode(self):
        self._mode = "dark" if self._mode == "light" else "light"
        ctk.set_appearance_mode(self._mode)

    # ---------- body ----------
    def _build_body(self):
        body = ctk.CTkFrame(self, corner_radius=0, fg_color=theme.PAGE_BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkScrollableFrame(body, width=250, corner_radius=0,
                                              fg_color=theme.SIDEBAR_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self._search_entry = ctk.CTkEntry(
            self.sidebar, textvariable=self._search_var,
            placeholder_text="Search menu... (Ctrl+F)")
        self._search_entry.pack(fill="x", padx=10, pady=(8, 8))
        self._search_var.trace_add("write", lambda *a: self._filter_nav())

        self._add_dashboard_button()
        self._build_nav()

        self.content = ctk.CTkFrame(body, corner_radius=0,
                                    fg_color=theme.PAGE_BG)
        self.content.grid(row=0, column=1, sticky="nsew", padx=16, pady=12)

    def _add_dashboard_button(self):
        def cmd():
            self._set_active(btn)
            self.show_dashboard()
        btn = ctk.CTkButton(self.sidebar, text="  Dashboard", anchor="w",
                            fg_color=theme.PRIMARY,
                            hover_color=theme.PRIMARY_DARK,
                            text_color="white",
                            font=(theme.FONT, 14, "bold"),
                            height=38, corner_radius=8, command=cmd)
        btn.pack(fill="x", padx=8, pady=(2, 6))
        self._active_btn = btn

    def _build_nav(self):
        curated = set()
        for section, items in NAV:
            resolved = []
            for label, kind, target in items:
                if kind == "m":
                    resolved.append((label, kind, target))
                else:
                    module, func = target
                    if _screen_exists(module, func):
                        resolved.append((label, kind, target))
                        curated.add((module, func))
            if resolved:
                self._add_section(section, resolved)
        extra = []
        for module, func, label in _discover_screens():
            if (module, func) in curated:
                continue
            extra.append((label, "s", (module, func)))
        if extra:
            extra.sort()
            self._add_section("More", extra)

    def _add_section(self, title, items):
        header = ctk.CTkButton(self.sidebar, text="  " + title.upper(),
                               anchor="w", fg_color="transparent",
                               hover_color=theme.SIDEBAR_HOVER,
                               text_color="#9db6cf",
                               font=(theme.FONT, 11, "bold"),
                               height=30, corner_radius=6)
        header.pack(fill="x", padx=8, pady=(8, 2))
        inner = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        inner.pack(fill="x", after=header)
        state = {"open": True}

        def toggle():
            state["open"] = not state["open"]
            if state["open"]:
                inner.pack(fill="x", after=header)
            else:
                inner.pack_forget()
        header.configure(command=toggle)

        for label, kind, target in items:
            self._add_nav_item(inner, label, kind, target)
        self._sections.append((header, inner, state))

    def _add_nav_item(self, parent, label, kind, target):
        def cmd():
            self._set_active(btn)
            if kind == "m":
                getattr(self, target)()
            else:
                module, func = target
                self._open(module, func)
        btn = ctk.CTkButton(parent, text="   " + label, anchor="w",
                            fg_color="transparent",
                            hover_color=theme.SIDEBAR_HOVER,
                            text_color="#e6eef6", font=(theme.FONT, 13),
                            height=32, corner_radius=6, command=cmd)
        btn.pack(fill="x", padx=8, pady=1)
        self._nav_buttons.append((label.lower(), btn, parent))

    def _set_active(self, btn):
        if self._active_btn is not None:
            try:
                if self._active_btn is not btn:
                    self._active_btn.configure(fg_color="transparent")
            except Exception:
                pass
        try:
            btn.configure(fg_color=theme.PRIMARY)
        except Exception:
            pass
        self._active_btn = btn

    def _filter_nav(self):
        q = self._search_var.get().strip().lower()
        if q:
            for header, inner, state in self._sections:
                inner.pack(fill="x", after=header)
                state["open"] = True
        for _l, btn, _p in self._nav_buttons:
            btn.pack_forget()
        for label_l, btn, parent in self._nav_buttons:
            if (not q) or (q in label_l):
                btn.pack(fill="x", padx=8, pady=1)

    # ---------- status bar ----------
    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=26, corner_radius=0,
                           fg_color="#dbe3ec")
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)
        self._status = ctk.CTkLabel(bar, text="Ready", text_color="#33475b",
                                    font=(theme.FONT, 11))
        self._status.pack(side="left", padx=12)
        ctk.CTkLabel(bar, text=COMPANY + "  -  BusyBooks",
                     text_color="#33475b",
                     font=(theme.FONT, 11)).pack(side="right", padx=12)

    def set_status(self, text):
        try:
            self._status.configure(text=text)
        except Exception:
            pass

    # ---------- shortcuts ----------
    def _bind_shortcuts(self):
        self.bind("<Control-f>", lambda e: self._search_entry.focus_set())
        self.bind("<Escape>", lambda e: self._search_clear())
        self.bind("<F5>", lambda e: self.show_dashboard())

    def _search_clear(self):
        self._search_var.set("")
        try:
            self.focus_set()
        except Exception:
            pass

    # ---------- core surface used by screens ----------
    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _title(self, text):
        theme.h1(self.content, text).pack(anchor="w", pady=(0, 10))
        self.set_status(text)

    def _open(self, module_name, func_name):
        self._clear()
        try:
            module = importlib.import_module(module_name)
            fn = getattr(module, func_name, None)
            if fn is None:
                self._not_built()
                return
            fn(self)
        except ModuleNotFoundError:
            self._not_built()
        except Exception as e:
            self._error(e)

    def _not_built(self):
        theme.h2(self.content, "That screen isn't built yet.").pack(pady=40)

    def _error(self, e):
        theme.h2(self.content, "Something went wrong").pack(pady=(40, 6))
        theme.muted(self.content, str(e)).pack()

    # ---------- dashboard ----------
    def _dashboard_metrics(self):
        d = {"ledgers": "-", "items": "-", "vouchers": "-",
             "stock": "-", "recv": "-", "pay": "-"}
        try:
            s = get_session()
            d["ledgers"] = str(s.query(Ledger).count())
            d["items"] = str(s.query(Item).count())
            d["vouchers"] = str(s.query(Voucher).count())
        except Exception:
            pass
        try:
            d["stock"] = _money(stock_mod.stock_value(get_session()))
        except Exception:
            pass
        try:
            from services import analytics
            recv, pay = analytics.receivables_payables()
            d["recv"] = _money(recv)
            d["pay"] = _money(pay)
        except Exception:
            pass
        return d

    def show_dashboard(self):
        self._clear()
        self._title("Dashboard")
        kpis = ctk.CTkFrame(self.content, fg_color="transparent")
        kpis.pack(fill="x")
        data = self._dashboard_metrics()
        cols = [
            ("Ledgers", data["ledgers"], theme.PRIMARY),
            ("Items", data["items"], theme.PRIMARY),
            ("Vouchers", data["vouchers"], theme.PRIMARY),
            ("Stock Value", data["stock"], theme.ACCENT),
            ("Receivables", data["recv"], theme.ACCENT),
            ("Payables", data["pay"], theme.DANGER),
        ]
        for i, (t, v, c) in enumerate(cols):
            card = theme.kpi_card(kpis, t, v, accent=c)
            card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
            kpis.grid_columnconfigure(i, weight=1)
        w = theme.card(self.content)
        w.pack(fill="both", expand=True, pady=(12, 0))
        theme.h2(w, "Welcome to " + COMPANY).pack(anchor="w", padx=18,
                                                  pady=(16, 4))
        theme.muted(w, "Use the menu on the left, or press Ctrl+F to "
                       "search it. Press F5 to return here.").pack(
            anchor="w", padx=18, pady=(0, 16))

    # ---------- master screens (delegated) ----------
    def show_groups(self):
        from ui import masters_screen
        masters_screen.groups(self)

    def show_ledgers(self):
        from ui import masters_screen
        masters_screen.ledgers(self)

    def show_items(self):
        from ui import masters_screen
        masters_screen.items(self)

    def show_units(self):
        from ui import masters_screen
        masters_screen.units(self)

    def show_stock(self):
        from ui import masters_screen
        masters_screen.stock(self)


def run():
    theme.apply(mode="light")
    App().mainloop()