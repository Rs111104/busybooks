import customtkinter as ctk
from ui import theme


def show_fin_year(app):
    from ui.app import _make_sheet, _selected_row
    from services import fin_year as fy
    app._clear()
    app._title("Financial Years")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)
    ref = {}

    name = ctk.CTkEntry(form, placeholder_text="FY name e.g. 2025-26",
                        width=150)
    name.pack(side="left", padx=3)
    start = ctk.CTkEntry(form, placeholder_text="Start YYYY-MM-DD",
                         width=140)
    start.pack(side="left", padx=3)
    end = ctk.CTkEntry(form, placeholder_text="End YYYY-MM-DD",
                       width=140)
    end.pack(side="left", padx=3)

    def refresh():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[y["id"], y["name"], y["start"], y["end"],
                 "YES" if y["active"] else ""]
                for y in fy.list_years()]
        ref["s"] = _make_sheet(holder, ["ID", "Name", "Start", "End",
                                        "Active"], rows)

    def add():
        if name.get().strip():
            fy.add_year(name.get(), start.get(), end.get())
            app.set_status("Financial year added")
        refresh()

    def activate():
        r = _selected_row(ref.get("s"))
        if not r:
            app.set_status("Select a year row first")
            return
        try:
            fy.set_active(int(r[0]))
            app.set_status("Set active: " + str(r[1]))
        except Exception as e:
            app.set_status("Error: " + str(e))
        refresh()

    theme.primary_button(form, "Add year", add).pack(side="left",
                                                     padx=6)
    theme.ghost_button(form, "Set active", activate).pack(side="left",
                                                          padx=4)
    refresh()