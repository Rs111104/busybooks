import customtkinter as ctk
from ui import theme


def show_gstjson(app):
    from ui.app import _make_sheet
    from services import gst_json
    app._clear()
    app._title("GSTR-1 JSON Export & Summaries")
    doc = gst_json.gstr1()
    top = ctk.CTkFrame(app.content, fg_color="transparent")
    top.pack(fill="x", pady=(0, 8))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    def show_b2b():
        for w in holder.winfo_children():
            w.destroy()
        rows = []
        for g in doc["b2b"]:
            for inv in g["inv"]:
                rows.append([g["ctin"], inv["inum"], inv["idt"],
                             inv["txval"], inv["camt"], inv["samt"],
                             inv["iamt"], inv["val"]])
        _make_sheet(holder, ["GSTIN", "Invoice", "Date", "Taxable",
                             "CGST", "SGST", "IGST", "Total"], rows)

    def show_b2c():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[b["rt"], b["pos"], b["txval"], b["camt"], b["samt"],
                 b["iamt"]] for b in doc["b2cs"]]
        _make_sheet(holder, ["Rate%", "POS", "Taxable", "CGST",
                             "SGST", "IGST"], rows)

    def show_hsn():
        for w in holder.winfo_children():
            w.destroy()
        rows = [[h["hsn_sc"], h["desc"], h["qty"], h["txval"], h["camt"],
                 h["samt"], h["iamt"]] for h in doc["hsn"]]
        _make_sheet(holder, ["HSN", "Description", "Qty", "Taxable",
                             "CGST", "SGST", "IGST"], rows)

    def export():
        from services import gst_json as gj
        try:
            path = gj.export_gstr1()
            app.set_status("GSTR-1 JSON saved: " + path)
        except Exception as e:
            app.set_status("Export failed: " + str(e))

    theme.primary_button(top, "B2B", show_b2b).pack(side="left", padx=4)
    theme.ghost_button(top, "B2C", show_b2c).pack(side="left", padx=4)
    theme.ghost_button(top, "HSN Summary", show_hsn).pack(side="left", padx=4)
    theme.primary_button(top, "Export JSON", export).pack(side="right", padx=4)
    show_b2b()