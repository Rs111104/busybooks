import customtkinter as ctk
from ui import theme


def show_ratios(app):
    from ui.app import _make_sheet
    from services import ratios
    app._clear()
    app._title("Key Ratios & Figures")
    data = ratios.ratios()
    grid = ctk.CTkFrame(app.content, fg_color="transparent")
    grid.pack(fill="both", expand=True)
    rows = [[name, val] for (name, val) in data]
    _make_sheet(grid, ["Metric", "Value"], rows)