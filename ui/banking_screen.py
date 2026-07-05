# ui/banking_screen.py
"""Banking suite screen: import a bank statement, auto-match, reconcile."""
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
from tksheet import Sheet

from services import banking


def _grid(parent, headers, height=300):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def _sel(sheet):
    try:
        rows = sheet.get_selected_rows()
        if rows:
            return sorted(rows)[0]
        cells = sheet.get_selected_cells()
        if cells:
            return sorted(cells)[0][0]
    except Exception:
        pass
    return None


def show_banking(app):
    app._clear()
    app._title("Banking Suite")

    banks = banking.bank_ledgers()
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_imp = tabs.add("Statement")
    t_sum = tabs.add("Summary")

    bar = ctk.CTkFrame(t_imp)
    bar.pack(fill="x", pady=5)
    bank_pick = ctk.CTkOptionMenu(bar, values=banks or ["(no bank ledgers)"],
                                  width=200)
    bank_pick.grid(row=0, column=0, padx=4, pady=5)
    chosen = {"path": None}
    path_lbl = ctk.CTkLabel(bar, text="No file chosen")
    path_lbl.grid(row=0, column=2, padx=8)
    lines_state = {"data": []}
    sheet = _grid(t_imp, ["id", "Date", "Description", "Ref", "Amount",
                          "Dr/Cr", "Reconciled"])

    def load_lines():
        rows = banking.list_lines(bank_pick.get())
        lines_state["data"] = rows
        sheet.set_sheet_data([[r["id"], r["Date"], r["Description"],
                               r["Ref"], r["Amount"], r["Dr/Cr"],
                               r["Reconciled"]] for r in rows])

    def choose_file():
        p = filedialog.askopenfilename(
            title="Choose bank statement CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if p:
            chosen["path"] = p
            path_lbl.configure(text=os.path.basename(p))

    def do_import():
        if not chosen["path"]:
            messagebox.showinfo("Info", "Choose a CSV file first.")
            return
        try:
            n = banking.import_statement_csv(bank_pick.get(), chosen["path"])
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Imported", f"{n} statement line(s) imported.")
        load_lines()

    def do_auto():
        try:
            m = banking.auto_match(bank_pick.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Auto-match", f"{m} line(s) matched.")
        load_lines()

    def toggle(value):
        r = _sel(sheet)
        if r is None or r >= len(lines_state["data"]):
            messagebox.showinfo("Info", "Click a line first.")
            return
        banking.set_reconciled(lines_state["data"][r]["id"], value)
        load_lines()

    ctk.CTkButton(bar, text="Choose CSV", command=choose_file).grid(
        row=0, column=1, padx=4)
    ctk.CTkButton(bar, text="Import", command=do_import).grid(
        row=0, column=3, padx=4)
    ctk.CTkButton(bar, text="Auto-match", command=do_auto).grid(
        row=0, column=4, padx=4)
    ctk.CTkButton(bar, text="Reconcile",
                  command=lambda: toggle(True)).grid(row=0, column=5, padx=4)
    ctk.CTkButton(bar, text="Unreconcile",
                  command=lambda: toggle(False)).grid(row=0, column=6, padx=4)

    # -------- Summary --------
    sf = ctk.CTkFrame(t_sum)
    sf.pack(fill="x", pady=5)
    sum_box = ctk.CTkLabel(t_sum, text="", justify="left",
                           font=ctk.CTkFont(size=15))
    sum_box.pack(anchor="w", pady=10)

    def load_summary():
        d = banking.summary(bank_pick.get())
        if not d:
            sum_box.configure(text="No data.")
            return
        sum_box.configure(text="\n".join(f"{k}: {v}" for k, v in d.items()))

    ctk.CTkButton(sf, text="Refresh summary", command=load_summary).grid(
        row=0, column=0, padx=4, pady=5)

    load_lines()