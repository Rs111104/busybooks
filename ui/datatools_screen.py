# ui/datatools_screen.py
"""Data & Year-end tools: backup/restore, export masters, closing balances."""
import os
import datetime
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import datatools


def show_datatools(app):
    app._clear()
    app._title("Data & Year-end")

    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_b = tabs.add("Backup / Restore")
    t_e = tabs.add("Export")
    t_y = tabs.add("Year-end")

    # -------- Backup / Restore --------
    bf = ctk.CTkFrame(t_b)
    bf.pack(fill="x", pady=6)
    backup_list = ctk.CTkOptionMenu(bf, values=datatools.list_backups()
                                    or ["(no backups)"], width=280)
    backup_list.grid(row=0, column=2, padx=6)

    def do_backup():
        try:
            path = datatools.backup_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Backup", f"Saved:\n{os.path.abspath(path)}")
        backup_list.configure(values=datatools.list_backups()
                              or ["(no backups)"])

    def do_restore():
        name = backup_list.get()
        if not name or name == "(no backups)":
            messagebox.showinfo("Info", "No backup selected.")
            return
        if not messagebox.askyesno("Confirm restore",
                                   "Restoring overwrites current company "
                                   "data. Continue?"):
            return
        try:
            datatools.restore_backup(name)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Restore",
                            "Done. Restart the app to reload data.")

    ctk.CTkButton(bf, text="Backup now", command=do_backup).grid(
        row=0, column=0, padx=6, pady=6)
    ctk.CTkButton(bf, text="Restore selected", command=do_restore).grid(
        row=0, column=1, padx=6)

    # -------- Export --------
    ef = ctk.CTkFrame(t_e)
    ef.pack(fill="x", pady=6)
    ctk.CTkLabel(t_e, text="Export ledgers and items to Excel files in the "
                           "'exports' folder.").pack(anchor="w")

    def do_export():
        try:
            paths = datatools.export_masters()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Export", "Saved:\n" + "\n".join(paths))

    ctk.CTkButton(ef, text="Export masters", command=do_export).grid(
        row=0, column=0, padx=6, pady=6)

    # -------- Year-end --------
    yf = ctk.CTkFrame(t_y)
    yf.pack(fill="x", pady=6)
    year_e = ctk.CTkEntry(yf, placeholder_text="Year", width=100)
    year_e.insert(0, str(datetime.date.today().year))
    year_e.grid(row=0, column=0, padx=6, pady=6)
    sheet = Sheet(t_y, headers=["Ledger", "Closing balance", "Dr/Cr"],
                  data=[], height=300)
    sheet.enable_bindings("single_select", "row_select", "arrowkeys",
                          "column_width_resize")
    sheet.pack(fill="both", expand=True, pady=8)

    def load_closing():
        rows = datatools.closing_balances(year_e.get()
                                          or datetime.date.today().year)
        sheet.set_sheet_data([[r["Ledger"], r["Closing balance"], r["Dr/Cr"]]
                              for r in rows])

    def do_carry():
        if not messagebox.askyesno(
                "Confirm carry forward",
                "This sets every ledger's opening balance to its current "
                "closing balance. Make a backup first. Continue?"):
            return
        try:
            datatools.carry_forward()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Done", "Opening balances carried forward.")
        load_closing()

    ctk.CTkButton(yf, text="Show closing balances",
                  command=load_closing).grid(row=0, column=1, padx=6)
    ctk.CTkButton(yf, text="Carry forward openings", fg_color="#b06a00",
                  hover_color="#8a5300", command=do_carry).grid(
        row=0, column=2, padx=6)
    load_closing()