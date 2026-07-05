import customtkinter as ctk
from ui import theme


def show_mrp(app):
    from services import mrp
    app._clear()
    app._title("MRP / Tax-Inclusive Billing")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=8)
    mrpv = ctk.CTkEntry(form, placeholder_text="MRP (incl. tax)",
                        width=130)
    mrpv.pack(side="left", padx=3)
    ratev = ctk.CTkEntry(form, placeholder_text="GST %", width=80)
    ratev.pack(side="left", padx=3)
    qtyv = ctk.CTkEntry(form, placeholder_text="Qty", width=70)
    qtyv.pack(side="left", padx=3)
    interv = ctk.StringVar(value="Intra")
    ctk.CTkOptionMenu(form, variable=interv,
                      values=["Intra", "Inter"], width=80).pack(
        side="left", padx=3)
    out = theme.h2(app.content, "")
    out.pack(anchor="w", pady=8)

    def calc():
        try:
            inter = interv.get() == "Inter"
            r = mrp.line_from_mrp(mrpv.get() or 0, qtyv.get() or 1,
                                  ratev.get() or 0, inter)
            out.configure(
                text=("Taxable: %.2f | CGST: %.2f | SGST: %.2f | "
                      "IGST: %.2f | Gross (MRP): %.2f"
                      % (r["taxable"], r["cgst"], r["sgst"],
                         r["igst"], r["gross"])))
        except Exception as e:
            out.configure(text="Error: " + str(e))

    theme.primary_button(form, "Compute", calc).pack(side="left",
                                                     padx=6)