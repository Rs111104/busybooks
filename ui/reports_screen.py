# ui/reports_screen.py -- viewer over the existing services.reports
import customtkinter as ctk
from ui import theme

# Display name -> no-argument function name in services.reports
_MAP = {
    "Trial Balance": "trial_balance",
    "Profit & Loss": "profit_and_loss",
    "Balance Sheet": "balance_sheet",
    "Day Book": "day_book",
    "GST Summary": "gst_summary",
    "Stock Summary": "stock_summary",
}


def _normalize(result):
    """Return (columns, rows-as-dicts) for any shape a report may return."""
    try:
        import pandas as pd
        if isinstance(result, pd.DataFrame):
            return [str(c) for c in result.columns], result.to_dict("records")
    except Exception:
        pass
    if result is None:
        return [], []
    if isinstance(result, dict):
        return ["Item", "Value"], [{"Item": str(k), "Value": v}
                                   for k, v in result.items()]
    if isinstance(result, (list, tuple)):
        result = list(result)
        if not result:
            return [], []
        first = result[0]
        if isinstance(first, dict):
            cols = []
            for row in result:
                for k in row.keys():
                    if str(k) not in cols:
                        cols.append(str(k))
            return cols, [dict(r) for r in result]
        if isinstance(first, (list, tuple)):
            cols = ["col%d" % i for i in range(len(first))]
            return cols, [dict(zip(cols, r)) for r in result]
        return ["Value"], [{"Value": v} for v in result]
    return ["Value"], [{"Value": result}]


def show_reports(app):
    from ui.app import _make_sheet
    from services import reports
    app._clear()
    app._title("Reports")
    bar = ctk.CTkFrame(app.content, fg_color="transparent")
    bar.pack(fill="x", pady=(0, 6))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    names = [n for n in _MAP if hasattr(reports, _MAP[n])]
    if hasattr(reports, "ledger_statement"):
        names.append("Ledger Statement")
    picker = ctk.CTkOptionMenu(bar, values=names or ["-"])
    picker.pack(side="left", padx=3)

    ledgers = []
    try:
        if hasattr(reports, "ledger_names"):
            ledgers = list(reports.ledger_names()) or []
    except Exception:
        ledgers = []
    ledger_pick = ctk.CTkOptionMenu(bar, values=ledgers or ["-"])
    ledger_pick.pack(side="left", padx=3)

    def view():
        for w in holder.winfo_children():
            w.destroy()
        choice = picker.get()
        try:
            if choice == "Ledger Statement":
                result = reports.ledger_statement(ledger_pick.get())
            else:
                result = getattr(reports, _MAP[choice])()
            cols, rows = _normalize(result)
            data = [[r.get(c, "") for c in cols] for r in rows]
            _make_sheet(holder, cols or ["(no data)"], data)
            app.set_status("Viewed: " + choice)
        except Exception as e:
            app.set_status("Error: " + str(e))

    theme.primary_button(bar, "View", view).pack(side="left", padx=6)
    view()