import customtkinter as ctk
from ui import theme


def show_mrp(app):
    from services import mrp
    app._clear()
    app._title("MRP / Tax-Inclusive Billing")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=(0, 8))
    mrp_e = ctk.CTkEntry(form, placeholder_text="MRP", width=100)
    mrp_e.pack(side="left", padx=3)
    gst_e = ctk.CTkEntry(form, placeholder_text="GST %", width=80)
    gst_e.pack(side="left", padx=3)
    qty_e = ctk.CTkEntry(form, placeholder_text="Qty", width=80)
    qty_e.pack(side="left", padx=3)
    scope = ctk.CTkOptionMenu(form, values=["Intra-state", "Inter-state"])
    scope.pack(side="left", padx=3)
    out = ctk.CTkLabel(app.content, text="", justify="left")
    out.pack(anchor="w", pady=8)

    def do():
        try:
            inter = scope.get() == "Inter-state"
            qty = float(qty_e.get() or 1)
            r = mrp.line_from_mrp(float(mrp_e.get()), qty,
                                  float(gst_e.get() or 0), inter)
            out.configure(text=(
                "Taxable: %.2f\nCGST: %.2f   SGST: %.2f   IGST: %.2f\n"
                "Gross (=MRP×Qty): %.2f"
                % (r["taxable"], r["cgst"], r["sgst"], r["igst"],
                   r["gross"])))
            app.set_status("Computed MRP breakup")
        except Exception as e:
            out.configure(text="Error: " + str(e))

    theme.primary_button(form, "Compute", do).pack(side="left", padx=6)