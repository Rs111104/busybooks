# ui/stock_screen.py
"""Stock Summary screen — shows current quantity & value of every item."""
import customtkinter as ctk
from tksheet import Sheet
from db.engine import get_session
from core import stock


def show_stock(app):
    app._clear()
    app._title("Stock Summary")
    s = get_session()
    try:
        rows = stock.summary(s)
    finally:
        s.close()
    data = [[r["item"], r["qty"], r["rate"], r["value"]] for r in rows]
    total = round(sum(r["value"] for r in rows), 2)
    sh = Sheet(app.content, headers=["Item", "Quantity", "Rate", "Value"],
               data=data, height=420)
    sh.enable_bindings("single_select", "row_select", "arrowkeys")
    sh.pack(fill="both", expand=True, pady=10)
    ctk.CTkLabel(app.content, text=f"Total stock value: {total}",
                 font=ctk.CTkFont(size=14, weight="bold")).pack(
        anchor="e", padx=8)