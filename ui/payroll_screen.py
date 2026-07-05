import customtkinter as ctk
from ui import theme
from datetime import date


def show_payroll(app):
    from ui.app import _make_sheet
    from services import payroll
    app._clear()
    app._title("Payroll")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=(0, 6))
    ctrl = ctk.CTkFrame(app.content, fg_color="transparent")
    ctrl.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    name = ctk.CTkEntry(form, placeholder_text="Employee name", width=150)
    name.pack(side="left", padx=3)
    basic = ctk.CTkEntry(form, placeholder_text="Basic", width=80)
    basic.pack(side="left", padx=3)
    hra = ctk.CTkEntry(form, placeholder_text="HRA", width=80)
    hra.pack(side="left", padx=3)
    allow = ctk.CTkEntry(form, placeholder_text="Allowances", width=90)
    allow.pack(side="left", padx=3)
    period = ctk.CTkEntry(ctrl, placeholder_text="Period YYYY-MM",
                          width=120)
    period.pack(side="left", padx=3)
    period.insert(0, date.today().strftime("%Y-%m"))

    def show_emps():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[e["id"], e["name"], e["basic"], e["hra"],
                 e["allowances"], e["pf_pct"], e["esi_pct"]]
                for e in payroll.list_employees()]
        _make_sheet(holder, ["ID", "Name", "Basic", "HRA",
                             "Allowances", "PF%", "ESI%"], rows)

    def show_slips():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[p["employee"], p["period"], p["gross"], p["pf"],
                 p["esi"], p["other_ded"], p["net"]]
                for p in payroll.payslips(period.get() or None)]
        _make_sheet(holder, ["Employee", "Period", "Gross", "PF",
                             "ESI", "Other ded", "Net"], rows)

    def add_emp():
        try:
            payroll.add_employee(name.get(), basic.get() or 0,
                                 hra.get() or 0, allow.get() or 0)
            app.set_status("Employee added")
        except Exception as e:
            app.set_status("Error: " + str(e))
        show_emps()

    def run():
        try:
            n = payroll.run_payroll(period.get())
            app.set_status("Generated %d payslips" % len(n))
        except Exception as e:
            app.set_status("Error: " + str(e))
        show_slips()

    theme.primary_button(form, "Add employee", add_emp).pack(
        side="left", padx=6)
    theme.primary_button(ctrl, "Run payroll", run).pack(side="left",
                                                        padx=6)
    theme.ghost_button(ctrl, "Employees", show_emps).pack(side="left",
                                                          padx=4)
    theme.ghost_button(ctrl, "Payslips", show_slips).pack(side="left",
                                                          padx=4)
    show_emps()