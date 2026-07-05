import customtkinter as ctk
from ui import theme


def show_report_columns(app):
    from ui.app import _make_sheet
    from services import report_columns as rc
    app._clear()
    app._title("Custom Report Columns")
    top = ctk.CTkFrame(app.content, fg_color="transparent")
    top.pack(fill="x", pady=(0, 4))
    colbar = ctk.CTkFrame(app.content, fg_color="transparent")
    colbar.pack(fill="x", pady=(0, 4))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    repv = ctk.StringVar(value=rc.reports()[0])
    checks = {}

    def build_checks(*_):
        for w in colbar.winfo_children():
            w.destroy()
        checks.clear()
        for col in rc.available_columns(repv.get()):
            var = ctk.StringVar(value="on")
            cb = ctk.CTkCheckBox(colbar, text=col, variable=var,
                                 onvalue="on", offvalue="off")
            cb.pack(side="left", padx=4)
            checks[col] = var

    ctk.CTkOptionMenu(top, variable=repv, values=rc.reports(),
                      command=build_checks).pack(side="left", padx=3)

    def preview():
        for w in holder.winfo_children():
            w.destroy()
        cols = [c for c, v in checks.items() if v.get() == "on"]
        rows = rc.project(rc.fetch_rows(repv.get()), cols)
        theme.h2(holder,
                 "%s (%d rows)" % (repv.get(), len(rows))).pack(
            anchor="w", pady=(0, 4))
        _make_sheet(holder, cols,
                    [[r.get(c) for c in cols] for r in rows])

    theme.primary_button(top, "Preview", preview).pack(side="left",
                                                       padx=6)
    build_checks()
    preview()