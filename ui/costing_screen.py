# ui/costing_screen.py
"""Cost centres, allocations, and budget-vs-actual screen."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import costing


def _grid(parent, headers, height=240):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def show_costing(app):
    app._clear()
    app._title("Cost Centres & Budgets")

    ledgers = costing.ledger_names()
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_cc = tabs.add("Cost centres")
    t_al = tabs.add("Allocations")
    t_bg = tabs.add("Budgets")

    # -------- Cost centres --------
    cf = ctk.CTkFrame(t_cc)
    cf.pack(fill="x", pady=5)
    cc_name = ctk.CTkEntry(cf, placeholder_text="Cost centre name", width=200)
    cc_name.grid(row=0, column=0, padx=4, pady=5)
    cc_parent = ctk.CTkOptionMenu(cf, values=["(none)"] +
                                  costing.cost_centre_names(), width=180)
    cc_parent.grid(row=0, column=1, padx=4)
    cc_sheet = _grid(t_cc, ["ID", "Name", "Parent"])

    def load_cc():
        rows = costing.list_cost_centres()
        cc_sheet.set_sheet_data([[r["id"], r["Name"], r["Parent"]]
                                 for r in rows])

    def save_cc():
        parent = cc_parent.get()
        parent = None if parent == "(none)" else parent
        try:
            costing.create_cost_centre(cc_name.get(), parent)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        cc_name.delete(0, "end")
        cc_parent.configure(values=["(none)"] + costing.cost_centre_names())
        al_cc.configure(values=costing.cost_centre_names() or ["(none)"])
        load_cc()

    ctk.CTkButton(cf, text="Add cost centre", command=save_cc).grid(
        row=0, column=2, padx=6)
    load_cc()

    # -------- Allocations --------
    af = ctk.CTkFrame(t_al)
    af.pack(fill="x", pady=5)
    al_cc = ctk.CTkOptionMenu(af, values=costing.cost_centre_names()
                              or ["(none)"], width=180)
    al_cc.grid(row=0, column=0, padx=4, pady=5)
    al_led = ctk.CTkOptionMenu(af, values=ledgers or ["(none)"], width=180)
    al_led.grid(row=0, column=1, padx=4)
    al_amt = ctk.CTkEntry(af, placeholder_text="Amount", width=120)
    al_amt.grid(row=0, column=2, padx=4)
    al_sheet = _grid(t_al, ["Cost centre", "Allocated"])

    def load_alloc():
        rows = costing.cost_centre_report()
        al_sheet.set_sheet_data([[r["Cost centre"], r["Allocated"]]
                                 for r in rows])

    def do_alloc():
        try:
            costing.allocate(al_cc.get(), al_led.get(), al_amt.get() or 0)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        al_amt.delete(0, "end")
        load_alloc()

    ctk.CTkButton(af, text="Allocate", command=do_alloc).grid(
        row=0, column=3, padx=6)
    load_alloc()

    # -------- Budgets --------
    bf = ctk.CTkFrame(t_bg)
    bf.pack(fill="x", pady=5)
    bg_led = ctk.CTkOptionMenu(bf, values=ledgers or ["(none)"], width=180)
    bg_led.grid(row=0, column=0, padx=4, pady=5)
    bg_period = ctk.CTkEntry(bf, placeholder_text="Period YYYY-MM", width=130)
    bg_period.grid(row=0, column=1, padx=4)
    bg_amt = ctk.CTkEntry(bf, placeholder_text="Budget amount", width=130)
    bg_amt.grid(row=0, column=2, padx=4)
    bg_view = ctk.CTkEntry(bf, placeholder_text="View period YYYY-MM",
                           width=160)
    bg_view.grid(row=1, column=0, padx=4, pady=5)
    bg_sheet = _grid(t_bg, ["Ledger", "Budget", "Actual", "Variance"])

    def save_budget():
        try:
            costing.set_budget(bg_led.get(), bg_period.get(),
                               bg_amt.get() or 0)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        bg_amt.delete(0, "end")
        messagebox.showinfo("Saved", "Budget saved.")

    def load_bva():
        period = bg_view.get().strip()
        if not period:
            messagebox.showinfo("Info", "Type a period like 2026-04.")
            return
        rows = costing.budget_vs_actual(period)
        bg_sheet.set_sheet_data([[r["Ledger"], r["Budget"], r["Actual"],
                                  r["Variance"]] for r in rows])

    ctk.CTkButton(bf, text="Save budget", command=save_budget).grid(
        row=0, column=3, padx=6)
    ctk.CTkButton(bf, text="Show budget vs actual", command=load_bva).grid(
        row=1, column=1, padx=6)