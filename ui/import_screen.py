# ui/import_screen.py
"""Import Data screen: bulk-load items and parties from Excel files."""
import customtkinter as ctk
from tkinter import filedialog, messagebox

from services import importer


def show_import(app):
    app._clear()
    app._title("Import Data from Excel")

    ctk.CTkLabel(app.content,
                 text="Import masters from an Excel (.xlsx) file. Column "
                      "headers are read automatically (case-insensitive).",
                 wraplength=760, justify="left").pack(anchor="w", pady=4)
    ctk.CTkLabel(app.content,
                 text="Items columns:   name, unit, hsn, gst, sale, purchase\n"
                      "Ledgers columns: name, group, opening, dc, party, "
                      "gstin, state, state_code",
                 justify="left", text_color="gray").pack(anchor="w", pady=6)

    def do_items():
        path = filedialog.askopenfilename(
            filetypes=[("Excel", "*.xlsx *.xls")])
        if not path:
            return
        try:
            c, sk = importer.import_items(path)
            messagebox.showinfo("Done", f"Items imported: {c}\nSkipped: {sk}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def do_ledgers():
        path = filedialog.askopenfilename(
            filetypes=[("Excel", "*.xlsx *.xls")])
        if not path:
            return
        try:
            c, sk = importer.import_ledgers(path)
            messagebox.showinfo("Done",
                                f"Ledgers imported: {c}\nSkipped: {sk}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(app.content, text="Import Items from Excel...",
                  command=do_items).pack(anchor="w", pady=6)
    ctk.CTkButton(app.content, text="Import Ledgers/Parties from Excel...",
                  command=do_ledgers).pack(anchor="w", pady=6)