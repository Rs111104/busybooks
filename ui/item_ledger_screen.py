import customtkinter as ctk
from ui import theme


def show_item_ledger(app):
    from ui.app import _make_sheet
    from services import item_ledger
    app._clear()
    app._title("Item Ledger")
    its = item_ledger.list_items()
    top = ctk.CTkFrame(app.content, fg_color="transparent")
    top.pack(fill="x", pady=(0, 8))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)
    if not its:
        theme.muted(holder,
                    "No items yet. Add items under Masters > Items.").pack(
            pady=20)
        return
    names = [n for (_id, n) in its]
    idmap = {n: i for (i, n) in its}
    var = ctk.StringVar(value=names[0])

    def load(name):
        for w in holder.winfo_children():
            w.destroy()
        data = item_ledger.item_ledger(idmap[name])
        grid = ctk.CTkFrame(holder, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        rows = [[r["date"], r["voucher"], r["in"], r["out"],
                 r["balance"], r["rate"], r["value"]] for r in data]
        _make_sheet(grid, ["Date", "Voucher", "In", "Out",
                           "Balance", "Rate", "Value"], rows)

    ctk.CTkLabel(top, text="Item:",
                 font=(theme.FONT, 12, "bold")).pack(side="left", padx=(0, 6))
    ctk.CTkOptionMenu(top, values=names, variable=var,
                      command=load).pack(side="left")
    load(names[0])