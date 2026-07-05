# ui/reports_screen.py
"""Reports screen: pick a report, view it in a grid, export or print."""
import importlib
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import reports

REPORTS = {
    "Trial Balance": reports.trial_balance,
    "Profit & Loss": reports.profit_and_loss,
    "Balance Sheet": reports.balance_sheet,
    "GST Summary": reports.gst_summary,
    "Stock Summary": reports.stock_summary,
    "Day Book": reports.day_book,
}


def show_reports(app):
    app._clear()
    app._title("Reports")
    state = {"headers": [], "rows": []}

    bar = ctk.CTkFrame(app.content)
    bar.pack(fill="x", pady=5)
    pick = ctk.CTkOptionMenu(bar, values=list(REPORTS.keys()) +
                             ["Ledger Statement"], width=200)
    pick.grid(row=0, column=0, padx=5, pady=5)
    ledger_pick = ctk.CTkOptionMenu(bar, values=reports.ledger_names() or
                                    ["(none)"], width=200)
    ledger_pick.grid(row=0, column=1, padx=5)
    ctk.CTkLabel(bar, text="(for Ledger Statement)").grid(row=0, column=2,
                                                          padx=4)

    holder = {"sheet": None}

    def render(headers, rows):
        state["headers"] = headers
        state["rows"] = rows
        data = [[r.get(h, "") for h in headers] for r in rows]
        if holder["sheet"] is None:
            sh = Sheet(app.content, headers=headers, data=data, height=430)
            sh.enable_bindings("single_select", "row_select", "arrowkeys",
                               "column_width_resize")
            sh.pack(fill="both", expand=True, pady=8)
            holder["sheet"] = sh
        else:
            holder["sheet"].headers(headers)
            holder["sheet"].set_sheet_data(data)

    def run():
        name = pick.get()
        if name == "Ledger Statement":
            rows = reports.ledger_statement(ledger_pick.get())
            headers = ["Date", "Voucher", "Debit", "Credit", "Balance"]
        else:
            rows = REPORTS[name]()
            headers = list(rows[0].keys()) if rows else ["(no data)"]
        render(headers, rows)

    def export():
        if not state["rows"]:
            messagebox.showinfo("Info", "Run a report first.")
            return
        try:
            mod = importlib.import_module("output.export")
        except ModuleNotFoundError:
            messagebox.showinfo("Coming up",
                                "Excel export arrives on Day 9 "
                                "(create output/export.py).")
            return
        try:
            path = mod.rows_to_excel(pick.get(), state["headers"],
                                     state["rows"])
            messagebox.showinfo("Exported", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(bar, text="Run", command=run).grid(row=0, column=3, padx=5)
    ctk.CTkButton(bar, text="Export to Excel", command=export).grid(
        row=0, column=4, padx=5)

    # ---- Print invoice PDF (output/pdf.py arrives Day 9) ----
    pdfbar = ctk.CTkFrame(app.content)
    pdfbar.pack(fill="x", pady=(0, 4))
    ctk.CTkLabel(pdfbar, text="Invoice number:").grid(row=0, column=0, padx=4)
    inv_e = ctk.CTkEntry(pdfbar, placeholder_text="e.g. INV/0001", width=160)
    inv_e.grid(row=0, column=1, padx=4, pady=5)

    def print_pdf():
        num = inv_e.get().strip()
        if not num:
            messagebox.showinfo("Info", "Type a voucher number first.")
            return
        try:
            mod = importlib.import_module("output.pdf")
        except ModuleNotFoundError:
            messagebox.showinfo("Coming up",
                                "PDF printing arrives on Day 9 "
                                "(create output/pdf.py).")
            return
        try:
            path = mod.invoice_pdf(num)
            messagebox.showinfo("Saved", f"PDF saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(pdfbar, text="Print Invoice PDF", command=print_pdf).grid(
        row=0, column=2, padx=5)

    run()