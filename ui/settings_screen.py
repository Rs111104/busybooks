# ui/settings_screen.py
"""Settings screen: appearance theme and a custom invoice footer."""
import customtkinter as ctk
from tkinter import messagebox

from utils.settings import get_setting, set_setting


def show_settings(app):
    app._clear()
    app._title("Settings")

    ctk.CTkLabel(app.content, text="Appearance").pack(anchor="w", pady=(6, 0))
    theme = ctk.CTkOptionMenu(
        app.content, values=["System", "Light", "Dark"],
        command=lambda v: (ctk.set_appearance_mode(v),
                           set_setting("theme", v)))
    theme.set(get_setting("theme", "System"))
    theme.pack(anchor="w", pady=4)

    ctk.CTkLabel(app.content, text="Invoice footer / terms").pack(
        anchor="w", pady=(10, 0))
    footer = ctk.CTkEntry(app.content, width=500)
    footer.insert(0, get_setting("invoice_footer",
                                 "Thank you for your business!"))
    footer.pack(anchor="w", pady=4)

    def save():
        set_setting("invoice_footer", footer.get())
        messagebox.showinfo("Saved", "Settings saved.")

    ctk.CTkButton(app.content, text="Save settings", command=save).pack(
        anchor="w", pady=10)
    ctk.CTkLabel(app.content,
                 text="Settings are stored in settings.json in your project "
                      "folder.", text_color="gray").pack(anchor="w", pady=(20, 0))