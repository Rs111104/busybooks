import customtkinter as ctk
from ui import theme


def show_upi(app):
    from services import upi
    app._clear()
    app._title("UPI Payment QR")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=8)
    vpa = ctk.CTkEntry(form, placeholder_text="UPI ID (name@bank)",
                       width=200)
    vpa.pack(side="left", padx=3)
    nm = ctk.CTkEntry(form, placeholder_text="Payee name", width=150)
    nm.pack(side="left", padx=3)
    amt = ctk.CTkEntry(form, placeholder_text="Amount", width=100)
    amt.pack(side="left", padx=3)

    def make():
        p = upi.make_upi_qr(vpa.get(), nm.get(), amt.get() or 0)
        if p == "LIB_MISSING":
            app.set_status("Run: pip install qrcode pillow")
        else:
            app.set_status("QR saved: " + str(p))

    theme.primary_button(form, "Generate QR", make).pack(side="left",
                                                         padx=6)
    theme.h2(app.content,
             "Scan the PNG in output/ with any UPI app.").pack(
        anchor="w", pady=8)