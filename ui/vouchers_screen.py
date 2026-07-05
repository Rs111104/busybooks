# ui/vouchers_screen.py
"""The Vouchers screen: create Payment/Receipt/Contra/Journal and see them.
Wired into ui/app.py.
"""
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import vouchers

_HELP = {
    "Payment": "Payment: Debit the party/expense you paid  →  Credit Cash/Bank.",
    "Receipt": "Receipt: Debit Cash/Bank  →  Credit the party/income you received from.",
    "Contra":  "Contra: move money between Cash/Bank. Debit where money goes IN  →  Credit where it comes FROM.",
    "Journal": "Journal: any adjustment. Debit one account  →  Credit another.",
}


def show_vouchers(app):
    app._clear()
    app._title("Vouchers")

    lmap = vouchers.list_ledger_options()
    names = list(lmap.keys()) or ["(no ledgers)"]

    form = ctk.CTkFrame(app.content)
    form.pack(fill="x", pady=5)

    vtype = ctk.CTkOptionMenu(form, values=vouchers.VOUCHER_TYPES, width=120)
    vtype.grid(row=0, column=0, padx=5, pady=5)
    debit = ctk.CTkOptionMenu(form, values=names, width=180)
    debit.grid(row=0, column=1, padx=5, pady=5)
    credit = ctk.CTkOptionMenu(form, values=names, width=180)
    credit.grid(row=0, column=2, padx=5, pady=5)
    amount = ctk.CTkEntry(form, placeholder_text="Amount", width=110)
    amount.grid(row=0, column=3, padx=5, pady=5)
    vdate = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD (blank=today)",
                         width=190)
    vdate.grid(row=0, column=4, padx=5, pady=5)

    ctk.CTkLabel(form, text="Type").grid(row=1, column=0)
    ctk.CTkLabel(form, text="Debit (Dr)").grid(row=1, column=1)
    ctk.CTkLabel(form, text="Credit (Cr)").grid(row=1, column=2)
    ctk.CTkLabel(form, text="Amount").grid(row=1, column=3)
    ctk.CTkLabel(form, text="Date").grid(row=1, column=4)

    help_lbl = ctk.CTkLabel(app.content, text=_HELP["Payment"],
                            text_color="gray")
    help_lbl.pack(anchor="w", padx=4, pady=(6, 0))
    vtype.configure(command=lambda c: help_lbl.configure(text=_HELP.get(c, "")))

    narration = ctk.CTkEntry(app.content,
                             placeholder_text="Narration (optional)", width=520)
    narration.pack(anchor="w", padx=4, pady=6)

    holder = {"sheet": None}

    def refresh():
        rows = vouchers.list_recent_vouchers()
        data = [[v["number"], v["type"], v["date"], v["total"],
                 v["narration"]] for v in rows]
        if holder["sheet"] is None:
            sh = Sheet(app.content,
                       headers=["Number", "Type", "Date", "Total", "Narration"],
                       data=data, height=320)
            sh.enable_bindings("single_select", "row_select", "arrowkeys")
            sh.pack(fill="both", expand=True, pady=10)
            holder["sheet"] = sh
        else:
            holder["sheet"].set_sheet_data(data)

    def save():
        if debit.get() not in lmap or credit.get() not in lmap:
            messagebox.showerror("Error", "Pick both a debit and a credit account.")
            return
        try:
            amt = float(amount.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number.")
            return
        d = None
        if vdate.get().strip():
            try:
                d = datetime.strptime(vdate.get().strip(), "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Error", "Date must look like 2026-07-02.")
                return
        try:
            num = vouchers.create_voucher(
                vtype.get(), lmap[debit.get()], lmap[credit.get()], amt,
                vdate=d, narration=narration.get().strip() or None)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Saved", f"{vtype.get()} saved as {num}.")
        amount.delete(0, "end")
        narration.delete(0, "end")
        refresh()

    ctk.CTkButton(form, text="Save voucher", command=save).grid(
        row=0, column=5, padx=8)

    refresh()