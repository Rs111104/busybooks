import customtkinter as ctk
from ui import theme


def show_aging(app):
    from ui.app import _make_sheet
    from services import aging
    app._clear()
    app._title("Receivables & Payables Aging")
    tabs = ctk.CTkFrame(app.content, fg_color="transparent")
    tabs.pack(fill="x", pady=(0, 8))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    def load(kind):
        for w in holder.winfo_children():
            w.destroy()
        data = (aging.receivable_aging() if kind == "Receivable"
                else aging.payable_aging())
        grand = sum(r["total"] for r in data)
        theme.h2(holder, "{} Aging    Total: Rs {:,.2f}".format(
            kind, grand)).pack(anchor="w", pady=(0, 6))
        grid = ctk.CTkFrame(holder, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        rows = [[r["party"], r["b0"], r["b1"], r["b2"], r["b3"], r["total"]]
                for r in data]
        _make_sheet(grid, ["Party", "0-30", "31-60", "61-90", "90+",
                           "Total"], rows)

    theme.primary_button(tabs, "Receivables",
                         lambda: load("Receivable")).pack(side="left", padx=4)
    theme.ghost_button(tabs, "Payables",
                       lambda: load("Payable")).pack(side="left", padx=4)
    load("Receivable")