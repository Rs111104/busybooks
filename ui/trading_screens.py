# ui/trading_screens.py
"""Sales / Purchase / Credit Note / Debit Note screens.
Pick a party, add item lines (GST auto-fills from the item), click Save.
"""
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import masters, trading

_SAVERS = {
    "Sales": trading.create_sales_invoice,
    "Purchase": trading.create_purchase,
    "CreditNote": trading.create_credit_note,
    "DebitNote": trading.create_debit_note,
}


def _sel_row(sheet):
    try:
        rows = sheet.get_selected_rows()
        if rows:
            return min(rows)
    except Exception:
        pass
    return None


def _build(app, title, vtype):
    app._clear()
    app._title(title)

    ledgers = masters.list_ledgers()
    pmap = {l["name"]: l["id"] for l in ledgers}
    pnames = list(pmap.keys()) or ["(no ledgers)"]
    items = masters.list_items()
    imap = {it["name"]: it for it in items}
    inames = list(imap.keys()) or ["(no items)"]
    use_purchase = vtype in ("Purchase", "DebitNote")

    top = ctk.CTkFrame(app.content)
    top.pack(fill="x", pady=5)
    ctk.CTkLabel(top, text="Party").grid(row=0, column=0, padx=4)
    party = ctk.CTkOptionMenu(top, values=pnames, width=220)
    party.grid(row=0, column=1, padx=4, pady=5)
    ctk.CTkLabel(top, text="Date").grid(row=0, column=2, padx=4)
    vdate = ctk.CTkEntry(top, placeholder_text="YYYY-MM-DD (blank=today)",
                         width=200)
    vdate.grid(row=0, column=3, padx=4)
    narration = ctk.CTkEntry(top, placeholder_text="Narration", width=260)
    narration.grid(row=0, column=4, padx=4)

    adder = ctk.CTkFrame(app.content)
    adder.pack(fill="x", pady=5)
    item_dd = ctk.CTkOptionMenu(adder, values=inames, width=200)
    item_dd.grid(row=0, column=0, padx=4, pady=5)
    qty_e = ctk.CTkEntry(adder, placeholder_text="Qty", width=80)
    qty_e.grid(row=0, column=1, padx=4)
    rate_e = ctk.CTkEntry(adder, placeholder_text="Rate", width=90)
    rate_e.grid(row=0, column=2, padx=4)
    gst_e = ctk.CTkEntry(adder, placeholder_text="GST %", width=70)
    gst_e.grid(row=0, column=3, padx=4)

    def on_item(name):
        it = imap.get(name)
        if it:
            rate_e.delete(0, "end")
            rate_e.insert(0, str(it["purchase_rate"] if use_purchase
                                 else it["sale_rate"]))
            gst_e.delete(0, "end")
            gst_e.insert(0, str(it["gst_rate"]))
    item_dd.configure(command=on_item)
    if inames and inames[0] in imap:
        on_item(inames[0])

    lines = []
    holder = {"sheet": None}
    totals_lbl = ctk.CTkLabel(app.content, text="",
                              font=ctk.CTkFont(size=14, weight="bold"))

    def refresh():
        data = [[l["name"], l["qty"], l["rate"], round(l["qty"] * l["rate"], 2),
                 l["gst_rate"]] for l in lines]
        if holder["sheet"] is None:
            sh = Sheet(app.content,
                       headers=["Item", "Qty", "Rate", "Amount", "GST %"],
                       data=data, height=240)
            sh.enable_bindings("single_select", "row_select", "arrowkeys")
            sh.pack(fill="both", expand=True, pady=8)
            holder["sheet"] = sh
        else:
            holder["sheet"].set_sheet_data(data)
        sub = sum(l["qty"] * l["rate"] for l in lines)
        tax = sum(l["qty"] * l["rate"] * l["gst_rate"] / 100 for l in lines)
        totals_lbl.configure(
            text=f"Subtotal: {round(sub, 2)}    GST: {round(tax, 2)}    "
                 f"Grand Total: {round(sub + tax, 2)}")

    def add_line():
        if item_dd.get() not in imap:
            messagebox.showerror("Error", "Pick an item first.")
            return
        try:
            qty = float(qty_e.get() or 0)
            rate = float(rate_e.get() or 0)
            gst = float(gst_e.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Qty, rate, GST must be numbers.")
            return
        if qty <= 0:
            messagebox.showerror("Error", "Qty must be greater than 0.")
            return
        it = imap[item_dd.get()]
        lines.append({"item_id": it["id"], "name": it["name"], "qty": qty,
                      "rate": rate, "gst_rate": gst})
        qty_e.delete(0, "end")
        refresh()

    def remove_line():
        r = _sel_row(holder["sheet"]) if holder["sheet"] else None
        if r is None or r >= len(lines):
            messagebox.showinfo("Info", "Click a line row first.")
            return
        lines.pop(r)
        refresh()

    ctk.CTkButton(adder, text="Add line", command=add_line).grid(
        row=0, column=4, padx=6)
    ctk.CTkButton(adder, text="Remove selected line", fg_color="#b03030",
                  hover_color="#8f2626", command=remove_line).grid(
        row=0, column=5, padx=6)

    totals_lbl.pack(anchor="e", padx=8, pady=(4, 0))

    def save():
        if party.get() not in pmap:
            messagebox.showerror("Error", "Pick a party.")
            return
        if not lines:
            messagebox.showerror("Error", "Add at least one item line.")
            return
        d = None
        if vdate.get().strip():
            try:
                d = datetime.strptime(vdate.get().strip(), "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Error", "Date must look like 2026-07-02.")
                return
        payload = [{"item_id": l["item_id"], "qty": l["qty"], "rate": l["rate"],
                    "gst_rate": l["gst_rate"]} for l in lines]
        try:
            num = _SAVERS[vtype](pmap[party.get()], payload, vdate=d,
                                 narration=narration.get().strip() or None)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Saved", f"{title} saved as {num}.")
        lines.clear()
        refresh()

    ctk.CTkButton(app.content, text=f"Save {title}", command=save).pack(
        anchor="e", padx=8, pady=8)
    refresh()


def show_sales(app):
    _build(app, "Sales Invoice", "Sales")


def show_purchase(app):
    _build(app, "Purchase", "Purchase")


def show_credit_note(app):
    _build(app, "Credit Note", "CreditNote")


def show_debit_note(app):
    _build(app, "Debit Note", "DebitNote")