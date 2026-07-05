import customtkinter as ctk
from ui import theme


def show_invoice_pdf(app):
    from ui.app import _make_sheet
    from services import invoice_pdf
    app._clear()
    app._title("Invoice PDF (barcode + UPI QR)")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    vid = ctk.CTkEntry(bar, placeholder_text="Sales voucher ID",
                       width=140)
    vid.pack(side="left", padx=3)
    vpa = ctk.CTkEntry(bar, placeholder_text="UPI ID (optional)",
                       width=170)
    vpa.pack(side="left", padx=3)

    def show_list():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[r["id"], r["number"], r["date"], r["total"]]
                for r in invoice_pdf.sales_vouchers()]
        theme.h2(holder, "Sales invoices").pack(anchor="w",
                                                pady=(0, 4))
        _make_sheet(holder, ["ID", "Number", "Date", "Total"], rows)

    def make():
        try:
            r = invoice_pdf.build(int(vid.get()), vpa.get(), "")
            if r.get("ok"):
                app.set_status("Saved: " + r["path"])
            else:
                app.set_status("Error: " + r.get("msg", "failed"))
        except Exception as e:
            app.set_status("Error: " + str(e))

    theme.primary_button(bar, "Generate PDF", make).pack(side="left",
                                                         padx=6)
    theme.ghost_button(bar, "List sales", show_list).pack(side="left",
                                                          padx=4)
    show_list()