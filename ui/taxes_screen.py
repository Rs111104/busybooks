# ui/taxes_screen.py
"""TDS / TCS screen: manage sections, record deductions/collections, report."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import taxes


def _grid(parent, headers, height=240):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def show_taxes(app):
    app._clear()
    app._title("TDS / TCS")
    taxes.seed_sections()

    parties = taxes.party_names()
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_sec = tabs.add("Sections")
    t_rec = tabs.add("Deduct / Collect")
    t_rep = tabs.add("Report")

    # -------- Sections --------
    sf = ctk.CTkFrame(t_sec)
    sf.pack(fill="x", pady=5)
    s_code = ctk.CTkEntry(sf, placeholder_text="Code e.g. 194C", width=130)
    s_code.grid(row=0, column=0, padx=4, pady=5)
    s_name = ctk.CTkEntry(sf, placeholder_text="Description", width=200)
    s_name.grid(row=0, column=1, padx=4)
    s_rate = ctk.CTkEntry(sf, placeholder_text="Rate %", width=80)
    s_rate.grid(row=0, column=2, padx=4)
    s_thr = ctk.CTkEntry(sf, placeholder_text="Threshold", width=110)
    s_thr.grid(row=0, column=3, padx=4)
    s_kind = ctk.CTkOptionMenu(sf, values=["TDS", "TCS"], width=90)
    s_kind.grid(row=0, column=4, padx=4)
    sec_sheet = _grid(t_sec, ["Code", "Name", "Rate", "Threshold", "Kind"])

    def load_sections():
        rows = taxes.list_sections()
        sec_sheet.set_sheet_data([[r["code"], r["name"], r["rate"],
                                   r["threshold"], r["kind"]] for r in rows])

    def save_section():
        try:
            taxes.add_section(s_code.get(), s_name.get(), s_rate.get() or 0,
                              s_thr.get() or 0, s_kind.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for w in (s_code, s_name, s_rate, s_thr):
            w.delete(0, "end")
        load_sections()
        r_sec.configure(values=[r["code"] for r in taxes.list_sections()]
                        or ["(none)"])

    ctk.CTkButton(sf, text="Save section", command=save_section).grid(
        row=0, column=5, padx=6)
    load_sections()

    # -------- Deduct / Collect --------
    rf = ctk.CTkFrame(t_rec)
    rf.pack(fill="x", pady=5)
    r_kind = ctk.CTkOptionMenu(rf, values=["TDS", "TCS"], width=90)
    r_kind.grid(row=0, column=0, padx=4, pady=5)
    sec_codes = [r["code"] for r in taxes.list_sections()]
    r_sec = ctk.CTkOptionMenu(rf, values=sec_codes or ["(none)"], width=120)
    r_sec.grid(row=0, column=1, padx=4)
    r_party = ctk.CTkOptionMenu(rf, values=parties or ["(no parties)"],
                                width=200)
    r_party.grid(row=0, column=2, padx=4)
    r_base = ctk.CTkEntry(rf, placeholder_text="Base amount", width=120)
    r_base.grid(row=0, column=3, padx=4)
    r_rate = ctk.CTkEntry(rf, placeholder_text="Rate % (blank = default)",
                          width=180)
    r_rate.grid(row=1, column=0, columnspan=2, padx=4, pady=5)
    r_out = ctk.CTkLabel(t_rec, text="", font=ctk.CTkFont(size=15))
    r_out.pack(anchor="w", pady=8)
    rec_sheet = _grid(t_rec, ["Date", "Kind", "Section", "Party", "Base",
                              "Rate", "Tax"])

    def load_records():
        rows = taxes.list_deductions()
        rec_sheet.set_sheet_data([[r["Date"], r["Kind"], r["Section"],
                                   r["Party"], r["Base"], r["Rate"], r["Tax"]]
                                  for r in rows])

    def do_record():
        try:
            rate = r_rate.get().strip()
            rate = float(rate) if rate else None
            tax = taxes.record(r_kind.get(), r_sec.get(), r_party.get(),
                               r_base.get() or 0, rate)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        r_out.configure(text=f"Recorded. Tax amount = {tax}")
        r_base.delete(0, "end")
        r_rate.delete(0, "end")
        load_records()

    ctk.CTkButton(rf, text="Record", command=do_record).grid(
        row=0, column=4, padx=6)
    load_records()

    # -------- Report --------
    pf = ctk.CTkFrame(t_rep)
    pf.pack(fill="x", pady=5)
    rep_sheet = _grid(t_rep, ["Kind", "Section", "Base total", "Tax total"])

    def load_report():
        rows = taxes.report()
        rep_sheet.set_sheet_data([[r["Kind"], r["Section"], r["Base total"],
                                   r["Tax total"]] for r in rows])

    ctk.CTkButton(pf, text="Refresh report", command=load_report).grid(
        row=0, column=0, padx=4, pady=5)
    load_report()