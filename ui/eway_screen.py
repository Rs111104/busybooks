import customtkinter as ctk
from ui import theme


def show_eway(app):
    from ui.app import _make_sheet
    from services import eway
    app._clear()
    app._title("E-Way Bill Generator")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    vid = ctk.CTkEntry(bar, placeholder_text="Sales voucher ID", width=140)
    vid.pack(side="left", padx=3)
    dist = ctk.CTkEntry(bar, placeholder_text="Distance km", width=100)
    dist.pack(side="left", padx=3)
    veh = ctk.CTkEntry(bar, placeholder_text="Vehicle no", width=110)
    veh.pack(side="left", padx=3)
    modev = ctk.StringVar(value="1")
    ctk.CTkOptionMenu(bar, variable=modev,
                      values=["1", "2", "3", "4"], width=60).pack(
        side="left", padx=3)

    def show_list():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[r["id"], r["number"], r["date"], r["total"]]
                for r in eway.sales_vouchers()]
        theme.h2(holder, "Sales invoices (use ID above)").pack(
            anchor="w", pady=(0, 4))
        _make_sheet(holder, ["ID", "Number", "Date", "Total"], rows)

    def make():
        try:
            r = eway.generate(int(vid.get()), dist.get() or 0,
                              modev.get(), veh.get())
            if not r:
                app.set_status("Voucher not found")
            else:
                app.set_status("E-Way Bill JSON saved: " + r["path"])
        except Exception as e:
            app.set_status("Error: " + str(e))

    theme.primary_button(bar, "Generate", make).pack(side="left", padx=6)
    theme.ghost_button(bar, "List sales", show_list).pack(
        side="left", padx=4)
    show_list()