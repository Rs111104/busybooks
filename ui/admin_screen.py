# ui/admin_screen.py
"""Backup & Users screen: manage users, view audit log, back up the company."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import auth
from utils import backup
from ui.app import COMPANY


def show_admin(app):
    app._clear()
    app._title("Backup & Users")

    # ---- Backup ----
    row = ctk.CTkFrame(app.content)
    row.pack(fill="x", pady=5)

    def do_backup():
        try:
            path = backup.backup_company(COMPANY)
            messagebox.showinfo("Backup done", f"Saved copy to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ctk.CTkButton(row, text="Back up this company now",
                  command=do_backup).pack(side="left", padx=5)

    # ---- Create user ----
    form = ctk.CTkFrame(app.content)
    form.pack(fill="x", pady=8)
    u_name = ctk.CTkEntry(form, placeholder_text="New username", width=170)
    u_name.grid(row=0, column=0, padx=5, pady=5)
    u_pass = ctk.CTkEntry(form, placeholder_text="Password", width=150,
                          show="*")
    u_pass.grid(row=0, column=1, padx=5)
    u_role = ctk.CTkOptionMenu(form, values=["operator", "admin"], width=120)
    u_role.grid(row=0, column=2, padx=5)

    users_holder = {"sheet": None}

    def refresh_users():
        rows = auth.list_users()
        data = [[u["username"], u["role"], u["active"]] for u in rows]
        if users_holder["sheet"] is None:
            sh = Sheet(app.content,
                       headers=["Username", "Role", "Active"], data=data,
                       height=180)
            sh.enable_bindings("single_select", "row_select")
            sh.pack(fill="x", pady=8)
            users_holder["sheet"] = sh
        else:
            users_holder["sheet"].set_sheet_data(data)

    def add_user():
        if not u_name.get().strip() or not u_pass.get():
            messagebox.showerror("Error", "Enter a username and password.")
            return
        try:
            auth.create_user(u_name.get().strip(), u_pass.get(),
                             u_role.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        u_name.delete(0, "end")
        u_pass.delete(0, "end")
        refresh_users()

    ctk.CTkButton(form, text="Add user", command=add_user).grid(
        row=0, column=3, padx=5)

    ctk.CTkLabel(app.content, text="Users",
                 font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w")
    refresh_users()

    # ---- Audit log ----
    ctk.CTkLabel(app.content, text="Recent activity (audit log)",
                 font=ctk.CTkFont(size=15, weight="bold")).pack(
        anchor="w", pady=(10, 0))
    audit = auth.recent_audit()
    adata = [[a["When"], a["Action"], a["Entity"], a["Detail"]]
             for a in audit]
    ash = Sheet(app.content,
                headers=["When", "Action", "Entity", "Detail"], data=adata,
                height=200)
    ash.enable_bindings("single_select", "row_select")
    ash.pack(fill="both", expand=True, pady=6)