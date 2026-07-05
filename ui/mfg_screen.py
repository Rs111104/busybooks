# ui/mfg_screen.py
"""Manufacturing screen: create Bills of Materials and run production."""
import customtkinter as ctk
from tkinter import messagebox
from tksheet import Sheet

from services import manufacturing as mfg


def _grid(parent, headers, height=240):
    sh = Sheet(parent, headers=headers, data=[], height=height)
    sh.enable_bindings("single_select", "row_select", "arrowkeys",
                       "column_width_resize")
    sh.pack(fill="both", expand=True, pady=8)
    return sh


def _sel(sheet):
    try:
        rows = sheet.get_selected_rows()
        if rows:
            return sorted(rows)[0]
        cells = sheet.get_selected_cells()
        if cells:
            return sorted(cells)[0][0]
    except Exception:
        pass
    return None


def show_mfg(app):
    app._clear()
    app._title("Manufacturing (Bill of Materials)")

    items = mfg.item_names()
    tabs = ctk.CTkTabview(app.content)
    tabs.pack(fill="both", expand=True)
    t_bom = tabs.add("BOMs")
    t_prod = tabs.add("Produce")

    # ---------- BOM builder ----------
    top = ctk.CTkFrame(t_bom)
    top.pack(fill="x", pady=5)
    bom_name = ctk.CTkEntry(top, placeholder_text="BOM name", width=170)
    bom_name.grid(row=0, column=0, padx=4, pady=5)
    prod_item = ctk.CTkOptionMenu(top, values=items or ["(no items)"],
                                  width=170)
    prod_item.grid(row=0, column=1, padx=4)
    out_qty = ctk.CTkEntry(top, placeholder_text="Output qty", width=90)
    out_qty.grid(row=0, column=2, padx=4)

    comp_frame = ctk.CTkFrame(t_bom)
    comp_frame.pack(fill="x", pady=5)
    comp_item = ctk.CTkOptionMenu(comp_frame, values=items or ["(no items)"],
                                  width=170)
    comp_item.grid(row=0, column=0, padx=4, pady=5)
    comp_qty = ctk.CTkEntry(comp_frame, placeholder_text="Qty per batch",
                            width=120)
    comp_qty.grid(row=0, column=1, padx=4)

    pending = []          # component rows being built
    comp_sheet = _grid(t_bom, ["Component", "Qty per batch"], height=150)

    def refresh_comps():
        comp_sheet.set_sheet_data([[c["item_name"], c["qty"]] for c in pending])

    def add_comp():
        try:
            q = float(comp_qty.get() or 0)
        except ValueError:
            messagebox.showerror("Error", "Qty must be a number.")
            return
        if q <= 0:
            messagebox.showerror("Error", "Qty must be greater than zero.")
            return
        pending.append({"item_name": comp_item.get(), "qty": q})
        comp_qty.delete(0, "end")
        refresh_comps()

    def clear_comps():
        pending.clear()
        refresh_comps()

    ctk.CTkButton(comp_frame, text="Add component", command=add_comp).grid(
        row=0, column=2, padx=4)
    ctk.CTkButton(comp_frame, text="Clear list", command=clear_comps).grid(
        row=0, column=3, padx=4)

    bom_list = _grid(t_bom, ["ID", "Name", "Product", "Output qty",
                             "Components"], height=180)

    def load_boms():
        rows = mfg.list_boms()
        bom_list.set_sheet_data([[r["id"], r["Name"], r["Product"],
                                  r["Output qty"], r["Components"]]
                                 for r in rows])
        return rows

    def save_bom():
        if not pending:
            messagebox.showerror("Error", "Add at least one component.")
            return
        try:
            mfg.create_bom(bom_name.get(), prod_item.get(),
                           out_qty.get() or 1, list(pending))
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        bom_name.delete(0, "end")
        out_qty.delete(0, "end")
        clear_comps()
        load_boms()
        refresh_prod_boms()
        messagebox.showinfo("Saved", "BOM saved.")

    ctk.CTkButton(top, text="Save BOM", command=save_bom).grid(
        row=0, column=3, padx=6)
    current_boms = load_boms()

    # ---------- Produce ----------
    pf = ctk.CTkFrame(t_prod)
    pf.pack(fill="x", pady=5)
    prod_map = {}

    def refresh_prod_boms():
        nonlocal prod_map
        rows = mfg.list_boms()
        prod_map = {f"{r['Name']} ({r['Product']})": r["id"] for r in rows}
        p_bom.configure(values=list(prod_map.keys()) or ["(no BOMs)"])

    p_bom = ctk.CTkOptionMenu(pf, values=["(loading)"], width=240)
    p_bom.grid(row=0, column=0, padx=4, pady=5)
    p_times = ctk.CTkEntry(pf, placeholder_text="Batches (1)", width=100)
    p_times.grid(row=0, column=1, padx=4)
    p_allow = ctk.CTkCheckBox(pf, text="Allow negative stock")
    p_allow.grid(row=0, column=2, padx=4)
    p_out = _grid(t_prod, ["Item", "Required", "In stock", "Short by"],
                  height=200)
    p_msg = ctk.CTkLabel(t_prod, text="")
    p_msg.pack(anchor="w", pady=6)

    def _bom_id():
        key = p_bom.get()
        if key not in prod_map:
            messagebox.showerror("Error", "Pick a BOM.")
            return None
        return prod_map[key]

    def do_shortage():
        bid = _bom_id()
        if bid is None:
            return
        try:
            rows = mfg.check_shortage(bid, p_times.get() or 1)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        p_out.set_sheet_data([[r["Item"], r["Required"], r["In stock"],
                               r["Short by"]] for r in rows])
        p_msg.configure(text="No shortages — ready to produce." if not rows
                        else "Shortages found (see grid).")

    def do_produce():
        bid = _bom_id()
        if bid is None:
            return
        try:
            num, cost = mfg.produce(bid, p_times.get() or 1,
                                    allow_negative=bool(p_allow.get()))
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        p_msg.configure(text=f"Production {num} done. Finished unit cost "
                             f"= {cost}")

    ctk.CTkButton(pf, text="Check shortage", command=do_shortage).grid(
        row=0, column=3, padx=4)
    ctk.CTkButton(pf, text="Produce", command=do_produce).grid(
        row=0, column=4, padx=4)
    refresh_prod_boms()