import customtkinter as ctk
from ui import theme


def show_barcode(app):
    from services import barcode_tool
    app._clear()
    app._title("Barcode Generator")
    names = barcode_tool.item_names()
    var = ctk.StringVar(value=(names[0] if names else ""))
    row = ctk.CTkFrame(app.content, fg_color="transparent")
    row.pack(fill="x", pady=8)
    ctk.CTkLabel(row, text="Item:").pack(side="left", padx=4)
    ctk.CTkOptionMenu(row, variable=var,
                      values=names or [""]).pack(side="left", padx=4)

    def one():
        p = barcode_tool.generate(var.get())
        if p == "LIB_MISSING":
            app.set_status("Run: pip install python-barcode pillow")
        else:
            app.set_status("Saved: " + str(p))

    def allb():
        r = barcode_tool.generate_all()
        if not r:
            app.set_status(
                "Run: pip install python-barcode pillow (or add items)")
        else:
            app.set_status("Generated %d barcodes in output/barcodes"
                           % len(r))

    theme.primary_button(row, "Generate", one).pack(side="left", padx=6)
    theme.ghost_button(row, "Generate all", allb).pack(side="left", padx=4)
    theme.h2(app.content,
             "PNG files are saved in output/barcodes/").pack(
        anchor="w", pady=8)