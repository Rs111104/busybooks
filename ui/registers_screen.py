import customtkinter as ctk
from ui import theme


def show_registers(app):
    from ui.app import _make_sheet
    from services import registers
    app._clear()
    app._title("Sales & Purchase Registers")
    tabs = ctk.CTkFrame(app.content, fg_color="transparent")
    tabs.pack(fill="x", pady=(0, 8))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    def load(kind):
        for w in holder.winfo_children():
            w.destroy()
        data, total = (registers.sales_register() if kind == "Sales"
                       else registers.purchase_register())
        theme.h2(holder, "{} Register    Total: Rs {:,.2f}".format(
            kind, total)).pack(anchor="w", pady=(0, 6))
        grid = ctk.CTkFrame(holder, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        rows = [[r["date"], r["number"], r["party"], r["amount"]]
                for r in data]
        _make_sheet(grid, ["Date", "Number", "Party", "Amount"], rows)

    theme.primary_button(tabs, "Sales", lambda: load("Sales")).pack(
        side="left", padx=4)
    theme.ghost_button(tabs, "Purchase", lambda: load("Purchase")).pack(
        side="left", padx=4)
    load("Sales")