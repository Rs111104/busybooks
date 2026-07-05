# ui/bank_screen.py
"""Bank Reconciliation screen: tick cleared entries, see book vs bank."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import bank


def _sel(sheet):
    try:
        rows = sheet.get_selected_rows()
        if rows:
            return min(rows)
    except Exception:
        pass
    return None


def show_bank(app):
    app._clear()
    app._title("Bank Reconciliation")
    state = {"rows": []}

    bar = ctk.CTkFrame(app.content)
    bar.pack(fill="x", pady=5)
    pick = ctk.CTkOptionMenu(bar, values=bank.ledger_names() or ["(none)"],
                             width=220)
    pick.grid(row=0, column=0, padx=5, pady=5)
    holder = {"sheet": None}
    lbl = ctk.CTkLabel(app.content, text="",
                       font=ctk.CTkFont(size=14, weight="bold"))

    def load():
        obj = bank.statement(pick.get())
        state["rows"] = obj["rows"]
        data = [["✔" if r["cleared"] else "", r["date"], r["voucher"],
                 r["debit"], r["credit"]] for r in obj["rows"]]
        if holder["sheet"] is None:
            sh = Sheet(app.content,
                       headers=["Cleared", "Date", "Voucher", "Debit",
                                "Credit"], data=data, height=380)
            sh.enable_bindings("single_select", "row_select", "arrowkeys")
            sh.pack(fill="both", expand=True, pady=8)
            holder["sheet"] = sh
        else:
            holder["sheet"].set_sheet_data(data)
        diff = round(obj["book_balance"] - obj["cleared_balance"], 2)
        lbl.configure(text=f"Book balance: {obj['book_balance']}     "
                           f"Cleared (bank) balance: {obj['cleared_balance']}"
                           f"     Difference: {diff}")

    def toggle():
        r = _sel(holder["sheet"]) if holder["sheet"] else None
        if r is None or r >= len(state["rows"]):
            messagebox.showinfo("Info", "Click a row first.")
            return
        row = state["rows"][r]
        bank.toggle_cleared(pick.get(), row["id"], not row["cleared"])
        load()

    ctk.CTkButton(bar, text="Load", command=load).grid(row=0, column=1, padx=5)
    ctk.CTkButton(bar, text="Toggle cleared on selected",
                  command=toggle).grid(row=0, column=2, padx=5)
    lbl.pack(anchor="e", padx=8)
    load()