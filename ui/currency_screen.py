# ui/currency_screen.py
"""Multi-currency screen: manage currencies/rates and a quick converter."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import currency


def _grid(parent, headers, height=240):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def show_currency(app):
    app._clear()
    app._title("Multi-currency")

    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_c = tabs.add("Currencies")
    t_x = tabs.add("Converter")

    top = ctk.CTkFrame(t_c)
    top.pack(fill="x", pady=5)
    ctk.CTkLabel(top, text="Base currency:").grid(row=0, column=0, padx=4)
    base_e = ctk.CTkEntry(top, width=90)
    base_e.insert(0, currency.get_base())
    base_e.grid(row=0, column=1, padx=4)

    def save_base():
        try:
            currency.set_base(base_e.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        messagebox.showinfo("Saved", "Base currency set.")
        refresh_dropdowns()

    ctk.CTkButton(top, text="Set base", command=save_base).grid(
        row=0, column=2, padx=6)

    form = ctk.CTkFrame(t_c)
    form.pack(fill="x", pady=5)
    e_code = ctk.CTkEntry(form, placeholder_text="Code (USD)", width=90)
    e_code.grid(row=0, column=0, padx=4, pady=5)
    e_name = ctk.CTkEntry(form, placeholder_text="Name", width=150)
    e_name.grid(row=0, column=1, padx=4)
    e_sym = ctk.CTkEntry(form, placeholder_text="Symbol", width=70)
    e_sym.grid(row=0, column=2, padx=4)
    e_rate = ctk.CTkEntry(form, placeholder_text="Rate to base", width=110)
    e_rate.grid(row=0, column=3, padx=4)
    sheet = _grid(t_c, ["ID", "Code", "Name", "Symbol", "Rate to base"])

    def load():
        rows = currency.list_currencies()
        sheet.set_sheet_data([[r["id"], r["Code"], r["Name"], r["Symbol"],
                               r["Rate to base"]] for r in rows])

    def add():
        try:
            currency.add_currency(e_code.get(), e_name.get(), e_sym.get(),
                                  e_rate.get() or 1)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for w in (e_code, e_name, e_sym, e_rate):
            w.delete(0, "end")
        load()
        refresh_dropdowns()

    ctk.CTkButton(form, text="Add / update", command=add).grid(
        row=0, column=4, padx=6)
    load()

    # -------- Converter --------
    cf = ctk.CTkFrame(t_x)
    cf.pack(fill="x", pady=8)
    amt = ctk.CTkEntry(cf, placeholder_text="Amount", width=120)
    amt.grid(row=0, column=0, padx=4, pady=5)
    from_m = ctk.CTkOptionMenu(cf, values=[currency.get_base()], width=100)
    from_m.grid(row=0, column=1, padx=4)
    to_m = ctk.CTkOptionMenu(cf, values=[currency.get_base()], width=100)
    to_m.grid(row=0, column=2, padx=4)
    out = ctk.CTkLabel(t_x, text="", font=ctk.CTkFont(size=16))
    out.pack(anchor="w", pady=8)

    def refresh_dropdowns():
        codes = [currency.get_base()] + [r["Code"] for r in
                                         currency.list_currencies()]
        seen = []
        for c in codes:
            if c not in seen:
                seen.append(c)
        from_m.configure(values=seen)
        to_m.configure(values=seen)

    def do_convert():
        try:
            val = currency.convert(amt.get() or 0, from_m.get(), to_m.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        out.configure(text=f"{amt.get()} {from_m.get()} = {val} "
                           f"{to_m.get()}")

    ctk.CTkButton(cf, text="Convert", command=do_convert).grid(
        row=0, column=3, padx=6)
    refresh_dropdowns()