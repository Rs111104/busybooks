# ui/register_screen.py
"""Voucher Register: filter, view details, and delete saved vouchers."""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from tksheet import Sheet

from services import voucher_admin

VTYPES = ["All", "Sales", "Purchase", "CreditNote", "DebitNote",
          "Payment", "Receipt", "Contra", "Journal", "StockJournal"]


def _sel(sheet):
    try:
        rows = sheet.get_selected_rows()
        if rows:
            return min(rows)
    except Exception:
        pass
    return None


def _parse(entry):
    t = entry.get().strip()
    if not t:
        return None
    try:
        return datetime.strptime(t, "%Y-%m-%d").date()
    except ValueError:
        return None


def show_register(app):
    app._clear()
    app._title("Voucher Register")
    state = {"rows": []}

    bar = ctk.CTkFrame(app.content)
    bar.pack(fill="x", pady=5)
    vtype = ctk.CTkOptionMenu(bar, values=VTYPES, width=150)
    vtype.grid(row=0, column=0, padx=5, pady=5)
    frm = ctk.CTkEntry(bar, placeholder_text="From YYYY-MM-DD", width=150)
    frm.grid(row=0, column=1, padx=5)
    to = ctk.CTkEntry(bar, placeholder_text="To YYYY-MM-DD", width=150)
    to.grid(row=0, column=2, padx=5)

    holder = {"sheet": None}

    def refresh():
        rows = voucher_admin.list_vouchers(vtype.get(), _parse(frm), _parse(to))
        state["rows"] = rows
        data = [[r["date"], r["vtype"], r["number"], r["party"], r["total"],
                 r["narration"]] for r in rows]
        if holder["sheet"] is None:
            sh = Sheet(app.content,
                       headers=["Date", "Type", "Number", "Party", "Total",
                                "Narration"], data=data, height=400)
            sh.enable_bindings("single_select", "row_select", "arrowkeys")
            sh.pack(fill="both", expand=True, pady=8)
            holder["sheet"] = sh
        else:
            holder["sheet"].set_sheet_data(data)

    def view():
        r = _sel(holder["sheet"]) if holder["sheet"] else None
        if r is None or r >= len(state["rows"]):
            messagebox.showinfo("Info", "Click a voucher row first.")
            return
        v = voucher_admin.get_voucher(state["rows"][r]["id"])
        lines = [f"{v['vtype']} {v['number']}   |   {v['date']}",
                 f"Party: {v['party']}", f"Total: {v['total']}",
                 "", "Ledger entries:"]
        for e in v["entries"]:
            lines.append(f"  {e['ledger']}   Dr {e['debit']}   Cr {e['credit']}")
        if v["items"]:
            lines.append("")
            lines.append("Items:")
            for it in v["items"]:
                lines.append(f"  {it['item']}  {it['qty']} x {it['rate']} "
                             f"= {it['amount']} (GST {it['gst_rate']}%)")
        messagebox.showinfo(f"Voucher {v['number']}", "\n".join(lines))

    def delete():
        r = _sel(holder["sheet"]) if holder["sheet"] else None
        if r is None or r >= len(state["rows"]):
            messagebox.showinfo("Info", "Click a voucher row first.")
            return
        row = state["rows"][r]
        if not messagebox.askyesno("Confirm",
                                   f"Delete {row['vtype']} {row['number']}?\n"
                                   "This also reverses its stock movement."):
            return
        try:
            voucher_admin.delete_voucher(row["id"])
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        refresh()

    ctk.CTkButton(bar, text="Show", command=refresh).grid(row=0, column=3,
                                                          padx=5)
    ctk.CTkButton(bar, text="View details", command=view).grid(row=0, column=4,
                                                               padx=5)
    ctk.CTkButton(bar, text="Delete selected", fg_color="#b03030",
                  hover_color="#8f2626", command=delete).grid(row=0, column=5,
                                                              padx=5)
    refresh()