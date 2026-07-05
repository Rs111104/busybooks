# ui/gst_returns_screen.py
"""GST Returns screen: pick GSTR-1 or GSTR-3B, view it, export to Excel."""
import importlib
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import gst_returns

RETURNS = {
    "GSTR-1 (Sales detail)": gst_returns.gstr1,
    "GSTR-3B (Summary)": gst_returns.gstr3b,
}


def show_gst_returns(app):
    app._clear()
    app._title("GST Returns")
    state = {"headers": [], "rows": []}

    bar = ctk.CTkFrame(app.content)
    bar.pack(fill="x", pady=5)
    pick = ctk.CTkOptionMenu(bar, values=list(RETURNS.keys()), width=220)
    pick.grid(row=0, column=0, padx=5, pady=5)
    holder = {"sheet": None}

    def render(headers, rows):
        state["headers"], state["rows"] = headers, rows
        data = [[r.get(h, "") for h in headers] for r in rows]
        if holder["sheet"] is None:
            sh = Sheet(app.content, headers=headers, data=data, height=420)
            sh.enable_bindings("single_select", "row_select", "arrowkeys",
                               "column_width_resize")
            sh.pack(fill="both", expand=True, pady=8)
            holder["sheet"] = sh
        else:
            holder["sheet"].headers(headers)
            holder["sheet"].set_sheet_data(data)

    def run():
        rows = RETURNS[pick.get()]()
        headers = list(rows[0].keys()) if rows else ["(no data)"]
        render(headers, rows)

    def export():
        if not state["rows"]:
            messagebox.showinfo("Info", "Run a return first.")
            return
        try:
            mod = importlib.import_module("output.export")
            path = mod.rows_to_excel(pick.get(), state["headers"],
                                     state["rows"])
            messagebox.showinfo("Exported", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(bar, text="Run", command=run).grid(row=0, column=1, padx=5)
    ctk.CTkButton(bar, text="Export to Excel", command=export).grid(
        row=0, column=2, padx=5)
    run()