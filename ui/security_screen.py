# ui/security_screen.py
"""Users & Security screen: manage users, role permissions, and audit log."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import security


def _grid(parent, headers, height=260):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def _sel(sheet):
    try:
        rows = sheet.get_selected_rows()
        if rows:
            return sorted(rows)[0]
        cells = sheet.get_selected_cells()
        if cells:
            return sorted(cells)[0][0]
    except Exception:
        pass
    return None


def show_security(app):
    app._clear()
    app._title("Users & Security")

    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_u = tabs.add("Users")
    t_p = tabs.add("Roles & Permissions")
    t_a = tabs.add("Audit log")

    # -------- Users --------
    uf = ctk.CTkFrame(t_u)
    uf.pack(fill="x", pady=5)
    u_name = ctk.CTkEntry(uf, placeholder_text="Username", width=150)
    u_name.grid(row=0, column=0, padx=4, pady=5)
    u_pass = ctk.CTkEntry(uf, placeholder_text="Password", width=150,
                          show="*")
    u_pass.grid(row=0, column=1, padx=4)
    u_role = ctk.CTkOptionMenu(uf, values=security.ROLES, width=120)
    u_role.grid(row=0, column=2, padx=4)
    u_state = {"data": []}
    u_sheet = _grid(t_u, ["id", "Username", "Role", "Active"])

    def load_users():
        rows = security.list_users()
        u_state["data"] = rows
        u_sheet.set_sheet_data([[r["id"], r["Username"], r["Role"],
                                 r["Active"]] for r in rows])

    def add_user():
        try:
            security.create_user(u_name.get(), u_pass.get(), u_role.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        u_name.delete(0, "end")
        u_pass.delete(0, "end")
        load_users()

    def _current():
        r = _sel(u_sheet)
        if r is None or r >= len(u_state["data"]):
            messagebox.showinfo("Info", "Click a user row first.")
            return None
        return u_state["data"][r]

    def change_role():
        u = _current()
        if not u:
            return
        security.set_role(u["id"], u_role.get())
        load_users()

    def toggle_active():
        u = _current()
        if not u:
            return
        security.set_active(u["id"], not (u["Active"] == "Yes"))
        load_users()

    def reset_pw():
        u = _current()
        if not u:
            return
        pw = u_pass.get().strip()
        if not pw:
            messagebox.showinfo("Info", "Type a new password in the box.")
            return
        security.reset_password(u["id"], pw)
        u_pass.delete(0, "end")
        messagebox.showinfo("Done", "Password reset.")

    ctk.CTkButton(uf, text="Add user", command=add_user).grid(
        row=0, column=3, padx=4)
    ctk.CTkButton(uf, text="Set role", command=change_role).grid(
        row=0, column=4, padx=4)
    ctk.CTkButton(uf, text="Toggle active", command=toggle_active).grid(
        row=0, column=5, padx=4)
    ctk.CTkButton(uf, text="Reset password", command=reset_pw).grid(
        row=0, column=6, padx=4)
    load_users()

    # -------- Roles & Permissions --------
    pf = ctk.CTkFrame(t_p)
    pf.pack(fill="x", pady=5)
    p_role = ctk.CTkOptionMenu(pf, values=security.ROLES, width=120)
    p_role.grid(row=0, column=0, padx=4, pady=5)
    checks = {}
    for i, feat in enumerate(security.FEATURES):
        cb = ctk.CTkCheckBox(pf, text=feat)
        cb.grid(row=1, column=i, padx=6, pady=6)
        checks[feat] = cb

    def load_perms(_=None):
        perms = security.load_permissions().get(p_role.get(), {})
        for feat, cb in checks.items():
            cb.select() if perms.get(feat) else cb.deselect()
    p_role.configure(command=load_perms)

    def save_perms():
        for feat, cb in checks.items():
            security.set_permission(p_role.get(), feat, bool(cb.get()))
        messagebox.showinfo("Saved", "Permissions saved.")

    ctk.CTkButton(pf, text="Save permissions", command=save_perms).grid(
        row=0, column=1, padx=4)
    load_perms()

    # -------- Audit log --------
    a_sheet = _grid(t_a, ["At", "User", "Action", "Entity", "Detail"])
    a_sheet.set_sheet_data([[r["At"], r["User"], r["Action"], r["Entity"],
                             r["Detail"]] for r in security.audit_log()])