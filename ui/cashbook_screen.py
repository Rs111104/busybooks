import customtkinter as ctk
from ui import theme


def show_cashbook(app):
    from ui.app import _make_sheet
    from services import cashbook
    app._clear()
    app._title("Cash / Bank Book")
    ledgers = cashbook.cash_bank_ledgers()
    top = ctk.CTkFrame(app.content, fg_color="transparent")
    top.pack(fill="x", pady=(0, 8))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)
    if not ledgers:
        theme.muted(holder,
                    "No Cash or Bank ledgers found. Create one under "
                    "Masters > Ledgers (name it with 'Cash' or 'Bank')."
                    ).pack(pady=20)
        return
    names = [n for (_id, n) in ledgers]
    idmap = {n: i for (i, n) in ledgers}
    var = ctk.StringVar(value=names[0])

    def load(name):
        for w in holder.winfo_children():
            w.destroy()
        data = cashbook.cashbook(idmap[name])
        grid = ctk.CTkFrame(holder, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        rows = [[r["date"], r["voucher"], r["type"], r["debit"],
                 r["credit"], r["balance"]] for r in data]
        _make_sheet(grid, ["Date", "Voucher", "Type", "Debit",
                           "Credit", "Balance"], rows)

    ctk.CTkLabel(top, text="Ledger:",
                 font=(theme.FONT, 12, "bold")).pack(side="left", padx=(0, 6))
    ctk.CTkOptionMenu(top, values=names, variable=var,
                      command=load).pack(side="left")
    load(names[0])