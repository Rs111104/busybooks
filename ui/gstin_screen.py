import customtkinter as ctk
from ui import theme


def show_gstin(app):
    from services import gstin
    app._clear()
    app._title("GSTIN Validator")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 8))
    entry = ctk.CTkEntry(bar, placeholder_text="Enter GSTIN", width=260)
    entry.pack(side="left", padx=3)
    out = ctk.CTkLabel(app.content, text="", justify="left")
    out.pack(anchor="w", pady=8)

    def do():
        r = gstin.validate(entry.get())
        if r["ok"]:
            out.configure(text="✅ %s  (state code %s)"
                          % (r["reason"], r.get("state_code", "")))
        else:
            out.configure(text="❌ " + r["reason"])
        app.set_status("Checked GSTIN")

    theme.primary_button(bar, "Validate", do).pack(side="left", padx=6)