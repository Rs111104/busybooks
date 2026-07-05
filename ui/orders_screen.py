# ui/orders_screen.py
"""Order processing screen: build quotations / orders / challans, see the order
register, view pending orders, and convert an order into an invoice.
"""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import orders


def _sel(sheet):
    try:
        rows = sheet.get_selected_rows()
        if rows:
            return min(rows)
    except Exception:
        pass
    try:
        cur = sheet.get_currently_selected()
        if cur is not None and getattr(cur, "row", None) is not None:
            return cur.row
    except Exception:
        pass
    return None


def show_orders(app):
    app._clear()
    app._title("Orders & Quotations")

    parties = orders.list_parties()
    items = orders.list_items()
    pmap = {p["name"]: p["id"] for p in parties}
    imap = {i["name"]: i for i in items}
    cart = []

    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_new = tabs.add("New document")
    t_reg = tabs.add("Order register")
    t_pend = tabs.add("Pending orders")

    # -------- New document --------
    top = ctk.CTkFrame(t_new)
    top.pack(fill="x", pady=5)
    otype = ctk.CTkOptionMenu(top, values=["Sales", "Purchase"], width=110)
    otype.grid(row=0, column=0, padx=5, pady=5)
    stage = ctk.CTkOptionMenu(top, values=["Quotation", "Order", "Challan"],
                              width=120)
    stage.grid(row=0, column=1, padx=5, pady=5)
    party = ctk.CTkOptionMenu(top,
                              values=list(pmap.keys()) or ["(no parties)"],
                              width=210)
    party.grid(row=0, column=2, padx=5, pady=5)

    line = ctk.CTkFrame(t_new)
    line.pack(fill="x", pady=5)
    item_pick = ctk.CTkOptionMenu(line,
                                  values=list(imap.keys()) or ["(no items)"],
                                  width=210)
    item_pick.grid(row=0, column=0, padx=4, pady=5)
    qty_e = ctk.CTkEntry(line, placeholder_text="Qty", width=80)
    qty_e.grid(row=0, column=1, padx=4)
    rate_e = ctk.CTkEntry(line, placeholder_text="Rate", width=90)
    rate_e.grid(row=0, column=2, padx=4)
    gst_e = ctk.CTkEntry(line, placeholder_text="GST %", width=70)
    gst_e.grid(row=0, column=3, padx=4)

    sheet = Sheet(t_new, headers=["Item", "Qty", "Rate", "GST %", "Amount"],
                  data=[], height=210)
    sheet.enable_bindings("single_select", "row_select", "arrowkeys")

    def fill_rate(_=None):
        it = imap.get(item_pick.get())
        if not it:
            return
        if not rate_e.get():
            rate_e.insert(0, str(it["rate"] if otype.get() == "Sales"
                                 else it["purchase_rate"]))
        if not gst_e.get():
            gst_e.insert(0, str(it["gst_rate"]))
    item_pick.configure(command=fill_rate)

    def refresh_cart():
        sheet.set_sheet_data([[c["name"], c["qty"], c["rate"], c["gst_rate"],
                               c["amount"]] for c in cart])

    def add_line():
        it = imap.get(item_pick.get())
        if not it:
            messagebox.showerror("Error", "Pick an item.")
            return
        try:
            qty = float(qty_e.get() or 0)
            rate = float(rate_e.get() or 0)
            gst = float(gst_e.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Qty, Rate, GST must be numbers.")
            return
        if qty <= 0:
            messagebox.showerror("Error", "Qty must be greater than 0.")
            return
        cart.append({"item_id": it["id"], "name": it["name"], "qty": qty,
                     "rate": rate, "gst_rate": gst,
                     "amount": round(qty * rate, 2)})
        for w in (qty_e, rate_e, gst_e):
            w.delete(0, "end")
        refresh_cart()

    def remove_line():
        r = _sel(sheet)
        if r is None or r >= len(cart):
            messagebox.showinfo("Info", "Click a line first.")
            return
        cart.pop(r)
        refresh_cart()

    def save_doc():
        if not cart:
            messagebox.showerror("Error", "Add at least one line.")
            return
        pid = pmap.get(party.get())
        try:
            num = orders.create_order(otype.get(), stage.get(), pid, cart)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Saved", f"{stage.get()} {num} saved.")
        cart.clear()
        refresh_cart()
        load_register()

    btns = ctk.CTkFrame(t_new)
    btns.pack(fill="x")
    ctk.CTkButton(btns, text="Add line", command=add_line).pack(
        side="left", padx=4, pady=4)
    ctk.CTkButton(btns, text="Remove line", command=remove_line).pack(
        side="left", padx=4)
    ctk.CTkButton(btns, text="Save document", command=save_doc).pack(
        side="left", padx=4)
    sheet.pack(fill="both", expand=True, pady=8)

    # -------- Register --------
    reg_bar = ctk.CTkFrame(t_reg)
    reg_bar.pack(fill="x", pady=5)
    reg_sheet = Sheet(t_reg, headers=["id", "Date", "Number", "Type", "Stage",
                                      "Party", "Total", "Status"], data=[],
                      height=380)
    reg_sheet.enable_bindings("single_select", "row_select", "arrowkeys")
    reg_state = {"data": []}

    def load_register():
        rows = orders.list_orders()
        reg_state["data"] = rows
        reg_sheet.set_sheet_data([[r["id"], r["Date"], r["Number"], r["Type"],
                                   r["Stage"], r["Party"], r["Total"],
                                   r["Status"]] for r in rows])

    def convert_sel():
        r = _sel(reg_sheet)
        if r is None or r >= len(reg_state["data"]):
            messagebox.showinfo("Info", "Click an order first.")
            return
        row = reg_state["data"][r]
        if not messagebox.askyesno("Confirm",
                                   f"Convert {row['Number']} to an invoice?"):
            return
        try:
            num = orders.convert_to_invoice(row["id"])
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Done", f"Invoice {num} created.")
        load_register()

    ctk.CTkButton(reg_bar, text="Refresh", command=load_register).pack(
        side="left", padx=4)
    ctk.CTkButton(reg_bar, text="Convert selected to Invoice",
                  command=convert_sel).pack(side="left", padx=4)
    reg_sheet.pack(fill="both", expand=True, pady=8)

    # -------- Pending --------
    pend_bar = ctk.CTkFrame(t_pend)
    pend_bar.pack(fill="x", pady=5)
    pend_type = ctk.CTkOptionMenu(pend_bar, values=["Sales", "Purchase"],
                                  width=110)
    pend_type.grid(row=0, column=0, padx=5)
    pend_sheet = Sheet(t_pend, headers=["Number", "Date", "Party", "Item",
                                        "Ordered", "Invoiced", "Pending"],
                       data=[], height=380)
    pend_sheet.enable_bindings("single_select", "row_select", "arrowkeys")

    def load_pending():
        rows = orders.pending_orders(pend_type.get())
        pend_sheet.set_sheet_data([[r["Number"], r["Date"], r["Party"],
                                    r["Item"], r["Ordered"], r["Invoiced"],
                                    r["Pending"]] for r in rows])

    ctk.CTkButton(pend_bar, text="Show pending", command=load_pending).grid(
        row=0, column=1, padx=5)
    pend_sheet.pack(fill="both", expand=True, pady=8)

    load_register()