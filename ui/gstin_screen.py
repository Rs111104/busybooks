import customtkinter as ctk
from ui import theme


def show_gstin(app):
    from services import gstin
    app._clear()
    app._title("GSTIN Validator")
    row = ctk.CTkFrame(app.content, fg_color="transparent")
    row.pack(fill="x", pady=8)
    ent = ctk.CTkEntry(row, placeholder_text="Enter 15-char GSTIN",
                       width=260)
    ent.pack(side="left", padx=4)
    result = theme.h2(app.content, "")
    result.pack(anchor="w", pady=8)

    def check():
        r = gstin.validate(ent.get())
        if r["valid"]:
            result.configure(
                text="\u2705 %s  |  State code: %s  PAN: %s"
                % (r["reason"], r["state_code"], r["pan"]))
        else:
            result.configure(text="\u274c " + r["reason"])

    theme.primary_button(row, "Validate", check).pack(side="left", padx=6)