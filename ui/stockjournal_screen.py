import customtkinter as ctk
from ui import theme


def show_stockjournal(app):
    from ui.app import _make_sheet
    from services import stock_journal as sj
    app._clear()
    app._title("Stock Journal (Transfer / Adjust)")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    items = sj.item_names()
    gods = sj.godown_names() or [""]
    itemv = ctk.StringVar(value=(items[0] if items else ""))
    fromv = ctk.StringVar(value=gods[0])
    tov = ctk.StringVar(value=gods[0])

    ctk.CTkLabel(form, text="Item:").pack(side="left", padx=3)
    ctk.CTkOptionMenu(form, variable=itemv,
                      values=items or [""]).pack(side="left", padx=3)
    ctk.CTkLabel(form, text="From:").pack(side="left", padx=3)
    ctk.CTkOptionMenu(form, variable=fromv, values=gods).pack(
        side="left", padx=3)
    ctk.CTkLabel(form, text="To:").pack(side="left", padx=3)
    ctk.CTkOptionMenu(form, variable=tov, values=gods).pack(
        side="left", padx=3)
    qty = ctk.CTkEntry(form, placeholder_text="Qty", width=80)
    qty.pack(side="left", padx=3)
    rate = ctk.CTkEntry(form, placeholder_text="Rate", width=80)
    rate.pack(side="left", padx=3)

    def refresh():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[r["id"], r["type"], r["item"], r["qty"], r["rate"],
                 r["date"], r["narration"]] for r in sj.journal_list()]
        theme.h2(holder, "Stock journal entries: %d" % len(rows)).pack(
            anchor="w", pady=(0, 4))
        _make_sheet(holder, ["ID", "Type", "Item", "Qty", "Rate",
                             "Date", "Narration"], rows)

    def do_transfer():
        r = sj.transfer(itemv.get(), fromv.get(), tov.get(),
                        qty.get() or 0, rate.get() or 0)
        app.set_status(r["msg"])
        refresh()

    def adj(direction):
        r = sj.adjust(itemv.get(), qty.get() or 0, direction,
                      fromv.get(), rate.get() or 0)
        app.set_status(r["msg"])
        refresh()

    theme.primary_button(form, "Transfer", do_transfer).pack(
        side="left", padx=6)
    theme.ghost_button(form, "Adjust +",
                       lambda: adj("In")).pack(side="left", padx=3)
    theme.ghost_button(form, "Adjust -",
                       lambda: adj("Out")).pack(side="left", padx=3)
    refresh()