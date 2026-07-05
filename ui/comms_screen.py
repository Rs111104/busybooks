# ui/comms_screen.py
"""Communication center screen: templates, send (single/bulk), outbox log."""
import os
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import comms


def _grid(parent, headers, height=200):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def show_comms(app):
    app._clear()
    app._title("Communication Center")

    contacts = comms.party_contacts()
    party_names = [c["name"] for c in contacts]
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_t = tabs.add("Templates")
    t_s = tabs.add("Send")
    t_l = tabs.add("Outbox log")

    # -------- Templates --------
    tf = ctk.CTkFrame(t_t)
    tf.pack(fill="x", pady=5)
    tp_name = ctk.CTkEntry(tf, placeholder_text="Template name", width=170)
    tp_name.grid(row=0, column=0, padx=4, pady=5)
    tp_chan = ctk.CTkOptionMenu(tf, values=["Email", "SMS", "WhatsApp"],
                                width=120)
    tp_chan.grid(row=0, column=1, padx=4)
    tp_subj = ctk.CTkEntry(tf, placeholder_text="Subject", width=260)
    tp_subj.grid(row=0, column=2, padx=4)
    ctk.CTkLabel(t_t, text="Body (use {party}, {company}, {date}, {phone}, "
                           "{email}, {gstin}):").pack(anchor="w")
    tp_body = ctk.CTkTextbox(t_t, height=120)
    tp_body.pack(fill="x", pady=6)
    tp_sheet = _grid(t_t, ["Name", "Channel", "Subject"])

    def load_templates():
        rows = comms.list_templates()
        tp_sheet.set_sheet_data([[r["name"], r["channel"], r["subject"]]
                                 for r in rows])

    def save_tmpl():
        try:
            comms.save_template(tp_name.get(), tp_chan.get(), tp_subj.get(),
                                tp_body.get("1.0", "end").strip())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        load_templates()
        refresh_send_templates()
        messagebox.showinfo("Saved", "Template saved.")

    def del_tmpl():
        nm = tp_name.get().strip()
        if not nm:
            messagebox.showinfo("Info", "Type the template name to delete.")
            return
        comms.delete_template(nm)
        load_templates()
        refresh_send_templates()

    ctk.CTkButton(tf, text="Save template", command=save_tmpl).grid(
        row=0, column=3, padx=4)
    ctk.CTkButton(tf, text="Delete by name", fg_color="#b03030",
                  hover_color="#8f2626", command=del_tmpl).grid(
        row=0, column=4, padx=4)
    load_templates()

    # -------- Send --------
    sf = ctk.CTkFrame(t_s)
    sf.pack(fill="x", pady=5)
    tmpl_map = {}

    def refresh_send_templates():
        nonlocal tmpl_map
        tmpl_map = {t["name"]: t for t in comms.list_templates()}
        send_tmpl.configure(values=list(tmpl_map.keys())
                            or ["(no templates)"])

    send_tmpl = ctk.CTkOptionMenu(sf, values=["(loading)"], width=180)
    send_tmpl.grid(row=0, column=0, padx=4, pady=5)
    send_party = ctk.CTkOptionMenu(sf, values=party_names
                                   or ["(no parties)"], width=200)
    send_party.grid(row=0, column=1, padx=4)
    preview = ctk.CTkTextbox(t_s, height=150)
    preview.pack(fill="x", pady=6)
    msg = ctk.CTkLabel(t_s, text="")
    msg.pack(anchor="w")

    def do_preview():
        t = tmpl_map.get(send_tmpl.get())
        if not t:
            messagebox.showinfo("Info", "Pick a template.")
            return
        body = comms.render(t["body"], send_party.get())
        subj = comms.render(t["subject"], send_party.get())
        preview.delete("1.0", "end")
        preview.insert("1.0", subj + "\n\n" + body)

    def do_send():
        t = tmpl_map.get(send_tmpl.get())
        if not t:
            messagebox.showinfo("Info", "Pick a template.")
            return
        path = comms.send(t["channel"], send_party.get(), t["subject"],
                          t["body"])
        msg.configure(text=f"Saved to outbox:\n{os.path.abspath(path)}")
        load_log()

    def do_bulk():
        t = tmpl_map.get(send_tmpl.get())
        if not t:
            messagebox.showinfo("Info", "Pick a template.")
            return
        n = comms.bulk_send(t["name"])
        msg.configure(text=f"Bulk: {n} message(s) written to the outbox.")
        load_log()

    ctk.CTkButton(sf, text="Preview", command=do_preview).grid(
        row=0, column=2, padx=4)
    ctk.CTkButton(sf, text="Send", command=do_send).grid(
        row=0, column=3, padx=4)
    ctk.CTkButton(sf, text="Bulk send to all parties",
                  command=do_bulk).grid(row=0, column=4, padx=4)
    refresh_send_templates()

    # -------- Outbox log --------
    log_sheet = _grid(t_l, ["At", "Channel", "Party", "To", "Subject",
                            "Status"])

    def load_log():
        rows = comms.log()
        log_sheet.set_sheet_data([[r["At"], r["Channel"], r["Party"],
                                   r["To"], r["Subject"], r["Status"]]
                                  for r in rows])

    load_log()