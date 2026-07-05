import customtkinter as ctk
from ui import theme


def show_multi_company(app):
    from ui.app import _make_sheet
    from services import multi_company as mc
    app._clear()
    app._title("Multi-Company Consolidated")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    def refresh():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[r["company"], r["sales"], r["purchase"], r["gross"]]
                for r in mc.consolidated()]
        _make_sheet(holder, ["Company", "Sales", "Purchase",
                             "Gross (S-P)"], rows)
        app.set_status("Consolidated %d companies" % max(len(rows) - 1, 0))

    theme.primary_button(bar, "Refresh", refresh).pack(side="left", padx=6)
    refresh()