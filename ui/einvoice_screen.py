# ui/einvoice_screen.py
"""E-Invoice & E-Way Bill screen: pick a sales invoice, validate, export JSON,
and make a QR PDF.
"""
import os
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import einvoice


def _grid(parent, headers, height=260):
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


def show_einvoice(app):
    app._clear()
    app._title("E-Invoice & E-Way Bill")

    invoices = einvoice.list_sales_invoices()
    sheet = _grid(app.content, ["ID", "Number", "Date", "Party", "Total"])
    sheet.set_sheet_data([[iv["id"], iv["number"], iv["date"], iv["party"],
                           iv["total"]] for iv in invoices])

    ctrl = ctk.CTkFrame(app.content)
    ctrl.pack(fill="x", pady=6)
    dist = ctk.CTkEntry(ctrl, placeholder_text="E-way distance km", width=150)
    dist.grid(row=0, column=0, padx=4, pady=5)
    vno = ctk.CTkEntry(ctrl, placeholder_text="Vehicle no", width=130)
    vno.grid(row=0, column=1, padx=4)
    msg = ctk.CTkLabel(app.content, text="", justify="left")
    msg.pack(anchor="w", pady=6)

    def _current_id():
        r = _sel(sheet)
        if r is None or r >= len(invoices):
            messagebox.showinfo("Info", "Click a sales invoice row first.")
            return None
        return invoices[r]["id"]

    def do_validate():
        vid = _current_id()
        if vid is None:
            return
        problems = einvoice.validate(vid)
        if problems:
            msg.configure(text="Not ready:\n- " + "\n- ".join(problems))
        else:
            msg.configure(text="Valid — ready to generate e-invoice.")

    def do_einvoice():
        vid = _current_id()
        if vid is None:
            return
        problems = einvoice.validate(vid)
        if problems:
            messagebox.showerror("Cannot generate",
                                 "Fix these first:\n- " + "\n- ".join(problems))
            return
        try:
            path = einvoice.export_einvoice(vid)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        msg.configure(text=f"E-invoice JSON saved:\n{os.path.abspath(path)}")

    def do_eway():
        vid = _current_id()
        if vid is None:
            return
        try:
            path = einvoice.export_ewaybill(vid, dist.get() or 0,
                                            vehicle_no=vno.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        msg.configure(text=f"E-way bill JSON saved:\n{os.path.abspath(path)}")

    def do_qr():
        vid = _current_id()
        if vid is None:
            return
        try:
            path = einvoice.make_qr_pdf(vid)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        msg.configure(text=f"QR PDF saved:\n{os.path.abspath(path)}")

    ctk.CTkButton(ctrl, text="Validate", command=do_validate).grid(
        row=0, column=2, padx=4)
    ctk.CTkButton(ctrl, text="Export e-invoice JSON",
                  command=do_einvoice).grid(row=0, column=3, padx=4)
    ctk.CTkButton(ctrl, text="Export e-way bill", command=do_eway).grid(
        row=0, column=4, padx=4)
    ctk.CTkButton(ctrl, text="QR code PDF", command=do_qr).grid(
        row=0, column=5, padx=4)