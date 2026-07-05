# ui/pos_screen.py
"""Point of Sale screen: pick items into a cart and check out fast."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import pos


def show_pos(app):
    app._clear()
    app._title("Point of Sale")

    items = pos.item_list()
    item_names = [i["name"] for i in items]
    by_name = {i["name"]: i for i in items}
    cart = []

    wrap = ctk.CTkFrame(app.content)
    wrap.pack(fill="both", expand=True)

    bar = ctk.CTkFrame(wrap)
    bar.pack(fill="x", pady=6)
    item_pick = ctk.CTkOptionMenu(bar, values=item_names or ["(no items)"],
                                  width=220)
    item_pick.grid(row=0, column=0, padx=4, pady=5)
    qty_e = ctk.CTkEntry(bar, placeholder_text="Qty", width=80)
    qty_e.insert(0, "1")
    qty_e.grid(row=0, column=1, padx=4)
    parties = ["Walk-in Customer"] + pos.party_list()
    party_pick = ctk.CTkOptionMenu(bar, values=parties, width=200)
    party_pick.grid(row=0, column=3, padx=4)

    sheet = Sheet(wrap, headers=["Item", "Qty", "Rate", "GST%", "Amount"],
                  data=[], height=320)
    sheet.enable_bindings("single_select", "row_select", "arrowkeys",
                          "column_width_resize")
    sheet.pack(fill="both", expand=True, pady=8)

    total_lbl = ctk.CTkLabel(wrap, text="Total: 0.00",
                             font=ctk.CTkFont(size=18, weight="bold"))
    total_lbl.pack(anchor="e", padx=10)

    def redraw():
        rows = []
        total = 0.0
        for c in cart:
            amt = c["qty"] * c["rate"]
            gst = amt * c["gst_rate"] / 100.0
            line_total = amt + gst
            total += line_total
            rows.append([c["name"], c["qty"], c["rate"], c["gst_rate"],
                         round(line_total, 2)])
        sheet.set_sheet_data(rows)
        total_lbl.configure(text=f"Total: {round(total, 2)}")

    def add_to_cart():
        it = by_name.get(item_pick.get())
        if not it:
            messagebox.showinfo("Info", "Pick an item.")
            return
        try:
            qty = float(qty_e.get() or 1)
        except ValueError:
            messagebox.showerror("Error", "Qty must be a number.")
            return
        cart.append({"item_id": it["id"], "name": it["name"], "qty": qty,
                     "rate": it["rate"], "gst_rate": it["gst_rate"]})
        redraw()

    def remove_selected():
        try:
            rows = sheet.get_selected_rows()
            idx = sorted(rows)[0] if rows else None
        except Exception:
            idx = None
        if idx is None or idx >= len(cart):
            messagebox.showinfo("Info", "Click a cart row first.")
            return
        cart.pop(idx)
        redraw()

    def checkout():
        if not cart:
            messagebox.showinfo("Info", "Cart is empty.")
            return
        try:
            num = pos.checkout(cart, party_pick.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Sale complete", f"Invoice created: {num}")
        cart.clear()
        redraw()

    ctk.CTkButton(bar, text="Add to cart", command=add_to_cart).grid(
        row=0, column=2, padx=6)
    ctk.CTkButton(bar, text="Remove line", command=remove_selected).grid(
        row=0, column=4, padx=6)
    ctk.CTkButton(bar, text="Checkout", fg_color="#2e7d32",
                  hover_color="#256428", command=checkout).grid(
        row=0, column=5, padx=6)
    redraw()