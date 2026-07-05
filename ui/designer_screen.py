# ui/designer_screen.py
"""Template Designer: customise invoice look, with a live preview."""
import customtkinter as ctk
from tkinter import messagebox

from services import doctemplate
from utils.settings import get_setting


def show_designer(app):
    app._clear()
    app._title("Template Designer")

    company = get_setting("company", "Demo Traders")
    t = doctemplate.load_template()

    body = ctk.CTkFrame(app.content)
    body.pack(fill="both", expand=True)
    left = ctk.CTkScrollableFrame(body, width=360)
    left.pack(side="left", fill="y", padx=6, pady=6)
    right = ctk.CTkFrame(body)
    right.pack(side="left", fill="both", expand=True, padx=6, pady=6)

    ctk.CTkLabel(left, text="Invoice header title").pack(anchor="w")
    e_header = ctk.CTkEntry(left, width=320)
    e_header.insert(0, t["header"])
    e_header.pack(pady=4)

    ctk.CTkLabel(left, text="Accent colour (hex)").pack(anchor="w")
    e_color = ctk.CTkEntry(left, width=320)
    e_color.insert(0, t["accent_color"])
    e_color.pack(pady=4)

    v_logo = ctk.CTkCheckBox(left, text="Show logo area")
    v_gstin = ctk.CTkCheckBox(left, text="Show GSTIN")
    v_hsn = ctk.CTkCheckBox(left, text="Show HSN column")
    v_bank = ctk.CTkCheckBox(left, text="Show bank details")
    for cb, key in ((v_logo, "show_logo"), (v_gstin, "show_gstin"),
                    (v_hsn, "show_hsn"), (v_bank, "show_bank_details")):
        cb.pack(anchor="w", pady=3)
        cb.select() if t[key] else cb.deselect()

    ctk.CTkLabel(left, text="Signatory line").pack(anchor="w")
    e_sign = ctk.CTkEntry(left, width=320)
    e_sign.insert(0, t["signatory"])
    e_sign.pack(pady=4)

    ctk.CTkLabel(left, text="Footer note").pack(anchor="w")
    e_footer = ctk.CTkEntry(left, width=320)
    e_footer.insert(0, t["footer_note"])
    e_footer.pack(pady=4)

    ctk.CTkLabel(left, text="Terms & conditions").pack(anchor="w")
    e_terms = ctk.CTkTextbox(left, width=320, height=90)
    e_terms.insert("1.0", t["terms"])
    e_terms.pack(pady=4)

    ctk.CTkLabel(right, text="Live preview",
                 font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
    preview = ctk.CTkTextbox(right, width=420)
    preview.pack(fill="both", expand=True, pady=6)

    def collect():
        return {
            "header": e_header.get(),
            "accent_color": e_color.get(),
            "show_logo": bool(v_logo.get()),
            "show_gstin": bool(v_gstin.get()),
            "show_hsn": bool(v_hsn.get()),
            "show_bank_details": bool(v_bank.get()),
            "signatory": e_sign.get(),
            "footer_note": e_footer.get(),
            "terms": e_terms.get("1.0", "end").strip(),
        }

    def refresh():
        merged = {**doctemplate.default_template(), **collect()}
        preview.delete("1.0", "end")
        preview.insert("1.0", doctemplate.preview_text(company, merged))

    def do_save():
        doctemplate.save_template(collect())
        messagebox.showinfo("Saved", "Template saved. New invoices use it.")
        refresh()

    btns = ctk.CTkFrame(right)
    btns.pack(fill="x")
    ctk.CTkButton(btns, text="Preview", command=refresh).pack(
        side="left", padx=4, pady=4)
    ctk.CTkButton(btns, text="Save template", command=do_save).pack(
        side="left", padx=4)
    refresh()