import customtkinter as ctk
from ui import theme


def show_production(app):
    from ui.app import _make_sheet
    from services import production as prod
    app._clear()
    app._title("Production & BOM")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=(0, 6))
    run = ctk.CTkFrame(app.content, fg_color="transparent")
    run.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    names = prod.item_names()
    prodv = ctk.StringVar(value=(names[0] if names else ""))
    compv = ctk.StringVar(value=(names[0] if names else ""))
    ctk.CTkLabel(form, text="Product:").pack(side="left", padx=3)
    ctk.CTkOptionMenu(form, variable=prodv,
                      values=names or [""]).pack(side="left", padx=3)
    ctk.CTkLabel(form, text="Component:").pack(side="left", padx=3)
    ctk.CTkOptionMenu(form, variable=compv,
                      values=names or [""]).pack(side="left", padx=3)
    cqty = ctk.CTkEntry(form, placeholder_text="Comp qty/unit",
                        width=110)
    cqty.pack(side="left", padx=3)
    pqty = ctk.CTkEntry(run, placeholder_text="Produce qty", width=110)
    pqty.pack(side="left", padx=3)

    def show_bom():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[b["component"], b["qty"]]
                for b in prod.bom_of(prodv.get())]
        theme.h2(holder, "BOM for " + prodv.get()).pack(
            anchor="w", pady=(0, 4))
        _make_sheet(holder, ["Component", "Qty per unit"], rows)

    def show_orders():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[o["id"], o["product"], o["qty"], o["date"], o["cost"],
                 o["unit_cost"]] for o in prod.orders()]
        theme.h2(holder, "Production orders").pack(anchor="w",
                                                   pady=(0, 4))
        _make_sheet(holder, ["ID", "Product", "Qty", "Date", "Cost",
                             "Unit cost"], rows)

    def add_bom():
        r = prod.add_bom(prodv.get(), compv.get(), cqty.get() or 0)
        app.set_status(r.get("msg", "BOM line added"))
        show_bom()

    def do_produce():
        r = prod.produce(prodv.get(), pqty.get() or 0)
        if r.get("ok"):
            app.set_status("Produced. Cost %.2f (unit %.2f)"
                           % (r["cost"], r["unit_cost"]))
        else:
            app.set_status("Error: " + r.get("msg", "failed"))
        show_orders()

    theme.primary_button(form, "Add BOM line", add_bom).pack(
        side="left", padx=6)
    theme.primary_button(run, "Produce", do_produce).pack(
        side="left", padx=6)
    theme.ghost_button(run, "Show BOM", show_bom).pack(side="left",
                                                       padx=3)
    theme.ghost_button(run, "Orders", show_orders).pack(side="left",
                                                        padx=3)
    show_bom()