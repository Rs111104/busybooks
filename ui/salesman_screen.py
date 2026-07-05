import customtkinter as ctk
from ui import theme


def show_salesman(app):
    from ui.app import _make_sheet
    from services import salesman
    app._clear()
    app._title("Salesman / Broker")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 6))
    asg = ctk.CTkFrame(app.content, fg_color="transparent")
    asg.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)
    idmap = {}

    newname = ctk.CTkEntry(bar, placeholder_text="New salesman",
                           width=160)
    newname.pack(side="left", padx=3)
    voucher_id = ctk.CTkEntry(asg, placeholder_text="Invoice voucher ID",
                              width=150)
    voucher_id.pack(side="left", padx=3)
    smvar = ctk.StringVar(value="")
    smmenu = ctk.CTkOptionMenu(asg, variable=smvar, values=[""])
    smmenu.pack(side="left", padx=3)

    def refresh_menus():
        sm = salesman.list_salesmen()
        names = [x["name"] for x in sm] or [""]
        smvar.set(names[0])
        smmenu.configure(values=names)
        idmap.clear()
        idmap.update({x["name"]: x["id"] for x in sm})

    def add_sm():
        if newname.get().strip():
            salesman.add_salesman(newname.get().strip())
            app.set_status("Salesman added")
        refresh_menus()
        report()

    def assign():
        try:
            sid = idmap.get(smvar.get())
            if sid and voucher_id.get():
                salesman.assign(int(voucher_id.get()), sid)
                app.set_status("Assigned")
        except Exception as e:
            app.set_status("Error: " + str(e))
        report()

    def report():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[r["salesman"], r["sales"]]
                for r in salesman.sales_by_salesman()]
        theme.h2(holder, "Sales by salesman").pack(anchor="w",
                                                   pady=(0, 4))
        _make_sheet(holder, ["Salesman", "Sales"], rows)
        rec = [[r["voucher_id"], r["number"], r["date"], r["total"],
                r["salesman"]] for r in salesman.recent_sales()]
        theme.h2(holder, "Recent sales (use ID to assign)").pack(
            anchor="w", pady=(8, 4))
        _make_sheet(holder, ["ID", "Number", "Date", "Total",
                             "Salesman"], rec)

    theme.primary_button(bar, "Add salesman", add_sm).pack(
        side="left", padx=6)
    theme.primary_button(asg, "Assign to invoice", assign).pack(
        side="left", padx=6)
    refresh_menus()
    report()