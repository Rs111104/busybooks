# ui/adv_financials_screen.py
"""Advanced financials screen: monthly P&L, cash flow, top customers/items."""
import datetime
import customtkinter as ctk
from tksheet import Sheet

from services import adv_financials as af


def _grid(parent, headers, height=320):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def show_adv_financials(app):
    app._clear()
    app._title("Advanced Financials")

    this_year = str(datetime.date.today().year)
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_pl = tabs.add("Monthly P&L")
    t_cf = tabs.add("Cash flow")
    t_tc = tabs.add("Top customers")
    t_ti = tabs.add("Top items")

    # -------- Monthly P&L --------
    pf = ctk.CTkFrame(t_pl)
    pf.pack(fill="x", pady=5)
    pl_year = ctk.CTkEntry(pf, placeholder_text="Year", width=100)
    pl_year.insert(0, this_year)
    pl_year.grid(row=0, column=0, padx=4, pady=5)
    pl_sheet = _grid(t_pl, ["Month", "Income", "Expense", "Profit"])

    def load_pl():
        rows = af.monthly_pl(pl_year.get() or this_year)
        pl_sheet.set_sheet_data([[r["Month"], r["Income"], r["Expense"],
                                  r["Profit"]] for r in rows])

    ctk.CTkButton(pf, text="Show", command=load_pl).grid(
        row=0, column=1, padx=4)
    load_pl()

    # -------- Cash flow --------
    cf = ctk.CTkFrame(t_cf)
    cf.pack(fill="x", pady=5)
    cf_year = ctk.CTkEntry(cf, placeholder_text="Year", width=100)
    cf_year.insert(0, this_year)
    cf_year.grid(row=0, column=0, padx=4, pady=5)
    cf_sheet = _grid(t_cf, ["Month", "Net cash flow"])

    def load_cf():
        rows = af.cash_flow(cf_year.get() or this_year)
        cf_sheet.set_sheet_data([[r["Month"], r["Net cash flow"]]
                                 for r in rows])

    ctk.CTkButton(cf, text="Show", command=load_cf).grid(
        row=0, column=1, padx=4)
    load_cf()

    # -------- Top customers --------
    tc_sheet = _grid(t_tc, ["Customer", "Sales"])
    tc_sheet.set_sheet_data([[r["Customer"], r["Sales"]]
                             for r in af.top_customers()])

    # -------- Top items --------
    ti_sheet = _grid(t_ti, ["Item", "Qty sold", "Value"])
    ti_sheet.set_sheet_data([[r["Item"], r["Qty sold"], r["Value"]]
                             for r in af.top_items()])