reorder_screen.pyimport customtkinter as ctk
from ui import theme


def show_reorder(app):
    from ui.app import _make_sheet
    from services import reorder
    app._clear()
    app._title("Low-Stock / Reorder Alerts")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 8))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    names = reorder.item_names()
    item_var = ctk.StringVar(value=(names[0] if names else ""))
    ctk.CTkLabel(bar, text="Item:").pack(side="left", padx=4)
    ctk.CTkOptionMenu(bar, variable=item_var,
                      values=names or [""]).pack(side="left", padx=4)
    lvl = ctk.CTkEntry(bar, placeholder_text="Reorder level", width=120)
    lvl.pack(side="left", padx=4)

    def refresh():
        for w in holder.winfo_children():
            w.destroy()
        data = reorder.alerts()
        theme.h2(holder, "Items at/below level: %d" % len(data)).pack(
            anchor="w", pady=(0, 6))
        rows = [[d["item"], d["qty"], d["level"], d["short"]]
                for d in data]
        _make_sheet(holder, ["Item", "In stock", "Reorder level",
                             "Shortfall"], rows)

    def save():
        try:
            reorder.set_level(item_var.get(), float(lvl.get() or 0))
            app.set_status("Reorder level saved")
        except Exception as e:
            app.set_status("Error: " + str(e))
        refresh()

    theme.primary_button(bar, "Set level", save).pack(side="left", padx=6)
    theme.ghost_button(bar, "Refresh", refresh).pack(side="left", padx=4)
    refresh()