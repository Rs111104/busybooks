# ui/pricing_screen.py
"""Pricing screen: price lists with tiers, discount schemes, and a rate check."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import pricing


def _grid(parent, headers, height=240):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def show_pricing(app):
    app._clear()
    app._title("Price Lists & Discounts")

    items = pricing.item_names()
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_pl = tabs.add("Price lists")
    t_sc = tabs.add("Discount schemes")
    t_rc = tabs.add("Rate check")

    # ---------- Price lists ----------
    head = ctk.CTkFrame(t_pl)
    head.pack(fill="x", pady=5)
    new_pl = ctk.CTkEntry(head, placeholder_text="New price list name",
                          width=200)
    new_pl.grid(row=0, column=0, padx=4, pady=5)
    pl_pick = ctk.CTkOptionMenu(head, values=pricing.list_price_lists()
                                or ["(none)"], width=180)
    pl_pick.grid(row=0, column=2, padx=12)

    def make_pl():
        try:
            pricing.create_price_list(new_pl.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        new_pl.delete(0, "end")
        pl_pick.configure(values=pricing.list_price_lists() or ["(none)"])
        messagebox.showinfo("Created", "Price list created.")

    ctk.CTkButton(head, text="Create list", command=make_pl).grid(
        row=0, column=1, padx=4)

    row2 = ctk.CTkFrame(t_pl)
    row2.pack(fill="x", pady=5)
    pi_item = ctk.CTkOptionMenu(row2, values=items or ["(no items)"],
                                width=170)
    pi_item.grid(row=0, column=0, padx=4, pady=5)
    pi_minqty = ctk.CTkEntry(row2, placeholder_text="Min qty (1)", width=100)
    pi_minqty.grid(row=0, column=1, padx=4)
    pi_rate = ctk.CTkEntry(row2, placeholder_text="Rate", width=100)
    pi_rate.grid(row=0, column=2, padx=4)
    pl_sheet = _grid(t_pl, ["Item", "Min qty", "Rate"])

    def load_prices():
        rows = pricing.list_prices(pl_pick.get())
        pl_sheet.set_sheet_data([[r["Item"], r["Min qty"], r["Rate"]]
                                 for r in rows])

    def save_price():
        if pl_pick.get() in ("(none)", ""):
            messagebox.showerror("Error", "Create/select a price list first.")
            return
        try:
            pricing.set_price(pl_pick.get(), pi_item.get(),
                              pi_rate.get() or 0, pi_minqty.get() or 1)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        pi_minqty.delete(0, "end")
        pi_rate.delete(0, "end")
        load_prices()

    ctk.CTkButton(row2, text="Set price", command=save_price).grid(
        row=0, column=3, padx=4)
    ctk.CTkButton(row2, text="Refresh", command=load_prices).grid(
        row=0, column=4, padx=4)

    # ---------- Discount schemes ----------
    sf = ctk.CTkFrame(t_sc)
    sf.pack(fill="x", pady=5)
    sc_name = ctk.CTkEntry(sf, placeholder_text="Scheme name", width=150)
    sc_name.grid(row=0, column=0, padx=4, pady=5)
    sc_type = ctk.CTkOptionMenu(sf, values=["percent", "flat"], width=100)
    sc_type.grid(row=0, column=1, padx=4)
    sc_value = ctk.CTkEntry(sf, placeholder_text="Value", width=90)
    sc_value.grid(row=0, column=2, padx=4)
    sc_min = ctk.CTkEntry(sf, placeholder_text="Min bill amount", width=130)
    sc_min.grid(row=0, column=3, padx=4)
    sc_sheet = _grid(t_sc, ["Name", "Type", "Value", "Min amount"])

    def load_schemes():
        rows = pricing.list_schemes()
        sc_sheet.set_sheet_data([[r["name"], r["type"], r["value"],
                                  r["min_amount"]] for r in rows])

    def save_scheme():
        try:
            pricing.add_scheme(sc_name.get(), sc_type.get(),
                               sc_value.get() or 0, sc_min.get() or 0)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for w in (sc_name, sc_value, sc_min):
            w.delete(0, "end")
        load_schemes()

    def del_scheme():
        nm = sc_name.get().strip()
        if not nm:
            messagebox.showinfo("Info", "Type the scheme name to delete it.")
            return
        pricing.remove_scheme(nm)
        load_schemes()

    ctk.CTkButton(sf, text="Save scheme", command=save_scheme).grid(
        row=0, column=4, padx=4)
    ctk.CTkButton(sf, text="Delete by name", fg_color="#b03030",
                  hover_color="#8f2626", command=del_scheme).grid(
        row=0, column=5, padx=4)
    load_schemes()

    # ---------- Rate check ----------
    rf = ctk.CTkFrame(t_rc)
    rf.pack(fill="x", pady=5)
    rc_item = ctk.CTkOptionMenu(rf, values=items or ["(no items)"], width=170)
    rc_item.grid(row=0, column=0, padx=4, pady=5)
    rc_qty = ctk.CTkEntry(rf, placeholder_text="Qty", width=80)
    rc_qty.grid(row=0, column=1, padx=4)
    rc_list = ctk.CTkOptionMenu(rf, values=["(none)"]
                                + pricing.list_price_lists(), width=170)
    rc_list.grid(row=0, column=2, padx=4)
    rc_out = ctk.CTkLabel(t_rc, text="", font=ctk.CTkFont(size=16))
    rc_out.pack(anchor="w", pady=10)

    def do_check():
        lst = rc_list.get()
        lst = None if lst == "(none)" else lst
        try:
            qty = float(rc_qty.get() or 1)
            rate = pricing.price_for(rc_item.get(), qty, lst)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        amount = rate * qty
        dname, disc = pricing.best_discount(amount)
        net = amount - disc
        txt = f"Rate: {rate}   Amount: {round(amount, 2)}"
        if dname:
            txt += f"   Discount ({dname}): -{disc}   Net: {round(net, 2)}"
        rc_out.configure(text=txt)

    ctk.CTkButton(rf, text="Check rate", command=do_check).grid(
        row=0, column=3, padx=4)