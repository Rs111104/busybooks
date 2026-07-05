# ui/inventory_screen.py
"""Advanced inventory screen: batches, expiry alerts, serial numbers, and
godown-to-godown transfers.
"""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import inventory_adv as inv


def _grid(parent, headers, height=300):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def show_inventory(app):
    app._clear()
    app._title("Advanced Inventory")

    items = inv.item_names()
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_batch = tabs.add("Batches")
    t_exp = tabs.add("Expiry alerts")
    t_serial = tabs.add("Serial numbers")
    t_xfer = tabs.add("Stock transfer")

    # -------- Batches --------
    bf = ctk.CTkFrame(t_batch)
    bf.pack(fill="x", pady=5)
    b_item = ctk.CTkOptionMenu(bf, values=items or ["(no items)"], width=170)
    b_item.grid(row=0, column=0, padx=4, pady=5)
    b_no = ctk.CTkEntry(bf, placeholder_text="Batch no", width=110)
    b_no.grid(row=0, column=1, padx=4)
    b_qty = ctk.CTkEntry(bf, placeholder_text="Qty", width=70)
    b_qty.grid(row=0, column=2, padx=4)
    b_rate = ctk.CTkEntry(bf, placeholder_text="Rate", width=80)
    b_rate.grid(row=0, column=3, padx=4)
    b_mfg = ctk.CTkEntry(bf, placeholder_text="Mfg YYYY-MM-DD", width=130)
    b_mfg.grid(row=1, column=0, padx=4, pady=5)
    b_exp = ctk.CTkEntry(bf, placeholder_text="Expiry YYYY-MM-DD", width=140)
    b_exp.grid(row=1, column=1, padx=4)
    b_sheet = _grid(t_batch, ["Item", "Batch", "Qty", "Rate", "Mfg", "Expiry"])

    def load_batches():
        rows = inv.list_batches()
        b_sheet.set_sheet_data([[r["Item"], r["Batch"], r["Qty"], r["Rate"],
                                 r["Mfg"], r["Expiry"]] for r in rows])

    def save_batch():
        try:
            inv.add_batch(b_item.get(), b_no.get(), b_qty.get() or 0,
                          b_rate.get() or 0, b_mfg.get(), b_exp.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for w in (b_no, b_qty, b_rate, b_mfg, b_exp):
            w.delete(0, "end")
        load_batches()

    ctk.CTkButton(bf, text="Add batch", command=save_batch).grid(
        row=1, column=2, columnspan=2, padx=4)
    load_batches()

    # -------- Expiry alerts --------
    ef = ctk.CTkFrame(t_exp)
    ef.pack(fill="x", pady=5)
    e_days = ctk.CTkEntry(ef, placeholder_text="Within days (30)", width=140)
    e_days.grid(row=0, column=0, padx=5, pady=5)
    e_sheet = _grid(t_exp, ["Item", "Batch", "Qty", "Expiry", "Days left",
                            "Status"])

    def load_expiry():
        try:
            days = int(e_days.get() or 30)
        except ValueError:
            days = 30
        rows = inv.expiry_report(days)
        e_sheet.set_sheet_data([[r["Item"], r["Batch"], r["Qty"], r["Expiry"],
                                 r["Days left"], r["Status"]] for r in rows])

    ctk.CTkButton(ef, text="Show expiring", command=load_expiry).grid(
        row=0, column=1, padx=5)
    load_expiry()

    # -------- Serial numbers --------
    sf = ctk.CTkFrame(t_serial)
    sf.pack(fill="x", pady=5)
    s_item = ctk.CTkOptionMenu(sf, values=items or ["(no items)"], width=170)
    s_item.grid(row=0, column=0, padx=4, pady=5)
    s_nos = ctk.CTkEntry(sf, placeholder_text="Serials, comma separated",
                         width=300)
    s_nos.grid(row=0, column=1, padx=4)
    s_sheet = _grid(t_serial, ["Item", "Serial", "Status"])

    def load_serials():
        rows = inv.list_serials()
        s_sheet.set_sheet_data([[r["Item"], r["Serial"], r["Status"]]
                                for r in rows])

    def save_serials():
        raw = [x for x in (s_nos.get() or "").split(",")]
        try:
            n = inv.add_serials(s_item.get(), raw)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        s_nos.delete(0, "end")
        messagebox.showinfo("Added", f"{n} serial number(s) added.")
        load_serials()

    ctk.CTkButton(sf, text="Add serials", command=save_serials).grid(
        row=0, column=2, padx=4)
    load_serials()

    # -------- Stock transfer --------
    xf = ctk.CTkFrame(t_xfer)
    xf.pack(fill="x", pady=5)
    godowns = inv.godown_names()
    x_item = ctk.CTkOptionMenu(xf, values=items or ["(no items)"], width=160)
    x_item.grid(row=0, column=0, padx=4, pady=5)
    x_from = ctk.CTkOptionMenu(xf, values=godowns or ["(no godowns)"],
                               width=140)
    x_from.grid(row=0, column=1, padx=4)
    x_to = ctk.CTkOptionMenu(xf, values=godowns or ["(no godowns)"], width=140)
    x_to.grid(row=0, column=2, padx=4)
    x_qty = ctk.CTkEntry(xf, placeholder_text="Qty", width=70)
    x_qty.grid(row=0, column=3, padx=4)
    x_rate = ctk.CTkEntry(xf, placeholder_text="Rate", width=80)
    x_rate.grid(row=0, column=4, padx=4)

    gf = ctk.CTkFrame(t_xfer)
    gf.pack(fill="x", pady=5)
    g_new = ctk.CTkEntry(gf, placeholder_text="New godown name", width=200)
    g_new.grid(row=0, column=0, padx=4, pady=5)
    msg = ctk.CTkLabel(t_xfer, text="")
    msg.pack(anchor="w", pady=6)

    def refresh_godowns():
        gd = inv.godown_names() or ["(no godowns)"]
        x_from.configure(values=gd)
        x_to.configure(values=gd)

    def make_godown():
        try:
            inv.add_godown(g_new.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        g_new.delete(0, "end")
        refresh_godowns()
        msg.configure(text="Godown created.")

    def do_transfer():
        try:
            num = inv.transfer_stock(x_item.get(), x_from.get(), x_to.get(),
                                     x_qty.get() or 0, x_rate.get() or 0)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        x_qty.delete(0, "end")
        x_rate.delete(0, "end")
        msg.configure(text=f"Transfer {num} recorded.")

    ctk.CTkButton(xf, text="Transfer", command=do_transfer).grid(
        row=0, column=5, padx=6)
    ctk.CTkButton(gf, text="Create godown", command=make_godown).grid(
        row=0, column=1, padx=4)