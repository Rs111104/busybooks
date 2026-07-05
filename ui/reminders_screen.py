import customtkinter as ctk
from ui import theme


def show_reminders(app):
    from ui.app import _make_sheet
    from services import reminders
    app._clear()
    app._title("Payment Reminders (Outstanding Receivables)")
    data = reminders.outstanding_parties()
    grid = ctk.CTkFrame(app.content, fg_color="transparent")
    grid.pack(fill="both", expand=True)
    if not data:
        theme.muted(grid,
                    "No outstanding receivables. You're all caught up.").pack(
            pady=20)
        return
    rows = [[r["party"], r["phone"], r["email"], r["due"]] for r in data]
    _make_sheet(grid, ["Party", "Phone", "Email", "Due"], rows)