import customtkinter as ctk
from ui import theme


def show_multi_company(app):
    from ui.app import _make_sheet
    from services import multi_company as mc
    app._clear()
    app._title("Multi-Company Consolidated Results")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    def refresh():
        for w in holder.winfo_children():
            w.destroy()
        data = mc.consolidated()
        rows = [[d["company"], d["sales"], d["purchase"], d["gross"]]
                for d in data]
        ts = sum(d["sales"] for d in data)
        tp = sum(d["purchase"] for d in data)
        rows.append(["TOTAL", round(ts, 2), round(tp, 2),
                     round(ts - tp, 2)])
        theme.h2(holder, "Companies: %d" % len(data)).pack(
            anchor="w", pady=(0, 4))
        _make_sheet(holder, ["Company", "Sales", "Purchase",
                             "Gross"], rows)

    theme.primary_button(bar, "Refresh", refresh).pack(side="left",
                                                       padx=6)
    refresh()