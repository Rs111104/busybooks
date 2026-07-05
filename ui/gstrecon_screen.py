import customtkinter as ctk
from ui import theme


def show_gstrecon(app):
    from ui.app import _make_sheet
    from services import gst_recon
    from tkinter import filedialog
    app._clear()
    app._title("GST Reconciliation (2A/2B vs Books)")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    def load():
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        for w in holder.winfo_children():
            w.destroy()
        try:
            data = gst_recon.reconcile(path)
        except Exception as e:
            app.set_status("Error: " + str(e))
            return
        rows = [[r["gstin"], r["inum"], r["portal"], r["books"],
                 r["status"]] for r in data]
        theme.h2(holder, "Rows: %d" % len(rows)).pack(anchor="w",
                                                      pady=(0, 4))
        _make_sheet(holder, ["Supplier GSTIN", "Invoice", "Portal",
                             "Books", "Status"], rows)

    theme.primary_button(bar, "Load 2A/2B JSON & reconcile",
                         load).pack(side="left", padx=6)
    theme.h2(app.content,
             "Pick the GSTR-2A/2B JSON downloaded from the portal.").pack(
        anchor="w", pady=8)