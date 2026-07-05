# ui/login_screen.py
"""Login window shown before the main app. Default: admin / admin."""
import customtkinter as ctk
from tkinter import messagebox

from db.engine import open_company
from services import auth
from ui.app import App, COMPANY


def run_login():
    open_company(COMPANY)
    auth.ensure_admin()

    win = ctk.CTk()
    win.title("BusyBooks - Login")
    win.geometry("380x300")

    ctk.CTkLabel(win, text="BusyBooks", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(28, 4))
    ctk.CTkLabel(win, text="Please sign in").pack()

    user = ctk.CTkEntry(win, placeholder_text="Username", width=220)
    user.pack(pady=(18, 6))
    pw = ctk.CTkEntry(win, placeholder_text="Password", width=220, show="*")
    pw.pack(pady=6)

    def do_login():
        u = auth.login(user.get().strip(), pw.get())
        if not u:
            messagebox.showerror("Login failed", "Wrong username or password.")
            return
        win.destroy()
        App().mainloop()

    pw.bind("<Return>", lambda e: do_login())
    ctk.CTkButton(win, text="Login", width=220, command=do_login).pack(pady=16)
    ctk.CTkLabel(win, text="First time? Use  admin / admin", text_color="gray").pack()
    win.mainloop()