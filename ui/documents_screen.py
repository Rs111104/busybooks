import customtkinter as ctk
from ui import theme


def show_documents(app):
    from ui.app import _make_sheet
    from services import documents as docs
    app._clear()
    app._title("Sales Documents (Indent/Quotation/Order/Challan)")
    lines = []
    top = ctk.CTkFrame(app.content, fg_color="transparent")
    top.pack(fill="x", pady=(0, 4))
    lf = ctk.CTkFrame(app.content, fg_color="transparent")
    lf.pack(fill="x", pady=(0, 4))
    act = ctk.CTkFrame(app.content, fg_color="transparent")
    act.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    dtypev = ctk.StringVar(value="Quotation")
    ctk.CTkOptionMenu(top, variable=dtypev,
                      values=docs.STAGES).pack(side="left", padx=3)
    parties = docs.party_names() or [""]
    partyv = ctk.StringVar(value=parties[0])
    ctk.CTkOptionMenu(top, variable=partyv,
                      values=parties).pack(side="left", padx=3)
    item = ctk.CTkEntry(lf, placeholder_text="Item", width=140)
    item.pack(side="left", padx=3)
    qty = ctk.CTkEntry(lf, placeholder_text="Qty", width=70)
    qty.pack(side="left", padx=3)
    rate = ctk.CTkEntry(lf, placeholder_text="Rate", width=80)
    rate.pack(side="left", padx=3)
    convid = ctk.CTkEntry(act, placeholder_text="Doc ID to advance",
                          width=150)
    convid.pack(side="left", padx=3)

    def refresh():
        for w in holder.winfo_children():
            w.destroy()
        theme.h2(holder, "Draft lines: %d" % len(lines)).pack(
            anchor="w", pady=(0, 4))
        _make_sheet(holder, ["Item", "Qty", "Rate"],
                    [[l["item"], l["qty"], l["rate"]] for l in lines])
        rows = [[d["id"], d["dtype"], d["number"], d["party"],
                 d["amount"], d["status"]]
                for d in docs.list_documents()]
        theme.h2(holder, "All documents").pack(anchor="w", pady=(8, 4))
        _make_sheet(holder, ["ID", "Type", "Number", "Party",
                             "Amount", "Status"], rows)

    def add_line():
        try:
            lines.append({"item": item.get(),
                          "qty": float(qty.get() or 0),
                          "rate": float(rate.get() or 0)})
        except Exception as e:
            app.set_status("Error: " + str(e))
        refresh()

    def create():
        if not lines:
            app.set_status("Add at least one line")
            return
        r = docs.create_document(dtypev.get(), partyv.get(),
                                 list(lines))
        app.set_status("Created " + r["number"])
        lines.clear()
        refresh()

    def convert():
        try:
            r = docs.convert(int(convid.get()))
            app.set_status(r.get("msg")
                           or ("Advanced to " + r.get("stage", "")))
        except Exception as e:
            app.set_status("Error: " + str(e))
        refresh()

    theme.primary_button(lf, "Add line", add_line).pack(side="left",
                                                        padx=6)
    theme.primary_button(act, "Create document", create).pack(
        side="left", padx=6)
    theme.ghost_button(act, "Advance stage", convert).pack(
        side="left", padx=4)
    refresh()