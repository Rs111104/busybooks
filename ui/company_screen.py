# ui/company_screen.py
"""Companies screen: create a new company and switch the active one."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import company_admin


def show_companies(app):
    app._clear()
    app._title("Companies")
    state = {"rows": []}

    ctk.CTkLabel(app.content,
                 text=f"Current company: {company_admin.current_company()}",
                 font=ctk.CTkFont(size=15, weight="bold")).pack(
        anchor="w", pady=4)

    form = ctk.CTkFrame(app.content)
    form.pack(fill="x", pady=6)
    name = ctk.CTkEntry(form, placeholder_text="New company name", width=200)
    name.grid(row=0, column=0, padx=4, pady=5)
    st = ctk.CTkEntry(form, placeholder_text="State", width=120)
    st.grid(row=0, column=1, padx=4)
    scode = ctk.CTkEntry(form, placeholder_text="State code", width=90)
    scode.grid(row=0, column=2, padx=4)
    gstin = ctk.CTkEntry(form, placeholder_text="GSTIN", width=170)
    gstin.grid(row=0, column=3, padx=4)

    holder = {"sheet": None}

    def refresh():
        rows = company_admin.all_companies()
        state["rows"] = rows
        cur = company_admin.current_company()
        data = [[c, "← current" if c == cur else ""] for c in rows]
        if holder["sheet"] is None:
            sh = Sheet(app.content, headers=["Company", ""], data=data,
                       height=300)
            sh.enable_bindings("single_select", "row_select")
            sh.pack(fill="both", expand=True, pady=8)
            holder["sheet"] = sh
        else:
            holder["sheet"].set_sheet_data(data)

    def create():
        try:
            company_admin.create_company(name.get(), st.get().strip(),
                                         scode.get().strip(),
                                         gstin.get().strip())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        name.delete(0, "end")
        refresh()
        messagebox.showinfo("Created",
                            "Company created. Select it and click "
                            "'Switch to selected' to open it.")

    def switch():
        try:
            rows = holder["sheet"].get_selected_rows()
            r = min(rows) if rows else None
        except Exception:
            r = None
        if r is None or r >= len(state["rows"]):
            messagebox.showinfo("Info", "Click a company row first.")
            return
        chosen = state["rows"][r]
        try:
            company_admin.switch_company(chosen)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Switch company",
                            f"Switched to '{chosen}'.\nClose the app and "
                            "re-run  python main.py  to load it.")
        refresh()

    ctk.CTkButton(form, text="Create company", command=create).grid(
        row=0, column=4, padx=6)

    btns = ctk.CTkFrame(app.content)
    btns.pack(fill="x")
    ctk.CTkButton(btns, text="Switch to selected", command=switch).pack(
        side="left", padx=4, pady=4)
    ctk.CTkButton(btns, text="Refresh", command=refresh).pack(
        side="left", padx=4)
    refresh()