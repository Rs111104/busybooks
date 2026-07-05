import customtkinter as ctk
from ui import theme


def show_batch(app):
    from ui.app import _make_sheet
    from services import batch
    app._clear()
    app._title("Batch & Serial Tracking")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    names = batch.item_names()
    itemv = ctk.StringVar(value=(names[0] if names else ""))
    ctk.CTkLabel(form, text="Item:").pack(side="left", padx=3)
    ctk.CTkOptionMenu(form, variable=itemv,
                      values=names or [""]).pack(side="left", padx=3)
    bno = ctk.CTkEntry(form, placeholder_text="Batch no", width=100)
    bno.pack(side="left", padx=3)
    qty = ctk.CTkEntry(form, placeholder_text="Qty", width=70)
    qty.pack(side="left", padx=3)
    exp = ctk.CTkEntry(form, placeholder_text="Expiry YYYY-MM-DD",
                       width=150)
    exp.pack(side="left", padx=3)

    def show_batches():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[b["item"], b["batch_no"], b["qty"], b["mfg"],
                 b["expiry"]] for b in batch.list_batches()]
        theme.h2(holder, "Batches").pack(anchor="w", pady=(0, 4))
        _make_sheet(holder, ["Item", "Batch", "Qty", "Mfg",
                             "Expiry"], rows)

    def show_expiring():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[b["item"], b["batch_no"], b["qty"], b["expiry"],
                 b["days_left"]] for b in batch.expiring_soon(30)]
        theme.h2(holder, "Expiring within 30 days").pack(
            anchor="w", pady=(0, 4))
        _make_sheet(holder, ["Item", "Batch", "Qty", "Expiry",
                             "Days left"], rows)

    def add():
        r = batch.add_batch(itemv.get(), bno.get(), qty.get() or 0,
                            0, None, exp.get())
        app.set_status(r.get("msg", "Batch added"))
        show_batches()

    theme.primary_button(form, "Add batch", add).pack(side="left",
                                                      padx=6)
    theme.ghost_button(form, "All batches", show_batches).pack(
        side="left", padx=3)
    theme.ghost_button(form, "Expiring", show_expiring).pack(
        side="left", padx=3)
    show_batches()