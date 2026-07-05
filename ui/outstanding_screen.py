# ui/outstanding_screen.py
"""Outstanding screen: receivables / payables with aging + Excel export."""
import importlib
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import outstanding

HEADERS = ["Party", "Balance", "0-30", "31-60", "61-90", "90+", "Phone"]


def show_outstanding(app):
    app._clear()
    app._title("Outstanding (Receivables / Payables)")
    state = {"rows": []}

    bar = ctk.CTkFrame(app.content)
    bar.pack(fill="x", pady=5)
    mode = ctk.CTkOptionMenu(bar, values=["Receivables (customers owe you)",
                                          "Payables (you owe suppliers)"],
                             width=280)
    mode.grid(row=0, column=0, padx=5, pady=5)
    holder = {"sheet": None}
    lbl = ctk.CTkLabel(app.content, text="",
                       font=ctk.CTkFont(size=14, weight="bold"))

    def run():
        rows = (outstanding.receivables()
                if mode.get().startswith("Receivables")
                else outstanding.payables())
        state["rows"] = rows
        data = [[r[h] for h in HEADERS] for r in rows]
        total = round(sum(r["Balance"] for r in rows), 2)
        if holder["sheet"] is None:
            sh = Sheet(app.content, headers=HEADERS, data=data, height=400)
            sh.enable_bindings("single_select", "row_select", "arrowkeys")
            sh.pack(fill="both", expand=True, pady=8)
            holder["sheet"] = sh
        else:
            holder["sheet"].set_sheet_data(data)
        lbl.configure(text=f"Total outstanding: {total}")

    def export():
        if not state["rows"]:
            messagebox.showinfo("Info", "Run first.")
            return
        try:
            mod = importlib.import_module("output.export")
            path = mod.rows_to_excel("Outstanding", HEADERS, state["rows"])
            messagebox.showinfo("Exported", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(bar, text="Show", command=run).grid(row=0, column=1, padx=5)
    ctk.CTkButton(bar, text="Export to Excel", command=export).grid(
        row=0, column=2, padx=5)
    lbl.pack(anchor="e", padx=8)
    run()