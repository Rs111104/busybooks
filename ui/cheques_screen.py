import customtkinter as ctk
from ui import theme


def show_cheques(app):
    from ui.app import _make_sheet, _selected_row
    from services import cheques
    app._clear()
    app._title("Cheque Register & PDC")
    form = ctk.CTkFrame(app.content, fg_color="transparent")
    form.pack(fill="x", pady=(0, 8))
    btns = ctk.CTkFrame(app.content, fg_color="transparent")
    btns.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)
    ref = {}

    party = ctk.CTkEntry(form, placeholder_text="Party", width=140)
    party.pack(side="left", padx=3)
    amount = ctk.CTkEntry(form, placeholder_text="Amount", width=90)
    amount.pack(side="left", padx=3)
    cno = ctk.CTkEntry(form, placeholder_text="Cheque no", width=100)
    cno.pack(side="left", padx=3)
    cdate = ctk.CTkEntry(form, placeholder_text="YYYY-MM-DD", width=100)
    cdate.pack(side="left", padx=3)
    dirv = ctk.StringVar(value="Incoming")
    ctk.CTkOptionMenu(form, variable=dirv,
                      values=["Incoming", "Outgoing"]).pack(
        side="left", padx=3)

    def refresh():
        for w in holder.winfo_children():
            w.destroy()
        data = cheques.list_cheques()
        rows = [[c["id"], c["date"], c["party"], c["cheque_no"],
                 c["amount"], c["direction"], c["status"]]
                for c in data]
        ref["s"] = _make_sheet(holder, ["ID", "Date", "Party",
                               "Cheque no", "Amount", "Dir",
                               "Status"], rows)

    def add():
        try:
            cheques.add_cheque(party.get(), amount.get() or 0,
                               cno.get(), "", cdate.get(), dirv.get())
            app.set_status("Cheque added")
        except Exception as e:
            app.set_status("Error: " + str(e))
        refresh()

    def _sel_id():
        r = _selected_row(ref.get("s"))
        if r:
            try:
                return int(r[0])
            except Exception:
                return None
        return None

    def mark(status):
        cid = _sel_id()
        if not cid:
            app.set_status("Select a cheque row first")
            return
        cheques.set_status(cid, status)
        app.set_status("Marked " + status)
        refresh()

    def prnt():
        cid = _sel_id()
        if not cid:
            app.set_status("Select a cheque row first")
            return
        p = cheques.print_cheque(cid)
        app.set_status("Saved: " + str(p) if p else "Failed")

    theme.primary_button(form, "Add", add).pack(side="left", padx=6)
    theme.ghost_button(btns, "Mark cleared",
                       lambda: mark("Cleared")).pack(side="left", padx=4)
    theme.ghost_button(btns, "Mark bounced",
                       lambda: mark("Bounced")).pack(side="left", padx=4)
    theme.primary_button(btns, "Print cheque", prnt).pack(side="left",
                                                          padx=4)
    refresh()