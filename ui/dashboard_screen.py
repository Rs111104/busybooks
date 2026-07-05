# ui/dashboard_screen.py
"""Charts dashboard: Sales vs Purchase + top items by stock value."""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services import reports


def show_dashboard(app):
    app._clear()
    app._title("Dashboard")

    daybook = reports.day_book()
    sales = sum(r["Total"] for r in daybook if r["Type"] == "Sales")
    purch = sum(r["Total"] for r in daybook if r["Type"] == "Purchase")
    stock = reports.stock_summary()
    top = sorted([r for r in stock if r["Value"]],
                 key=lambda r: r["Value"], reverse=True)[:5]

    fig = Figure(figsize=(9, 4), dpi=100)
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.bar(["Sales", "Purchase"], [sales, purch],
            color=["#2b6cb0", "#dd6b20"])
    ax1.set_title("Sales vs Purchase")
    ax2 = fig.add_subplot(1, 2, 2)
    if top:
        ax2.barh([t["Item"] for t in top][::-1],
                 [t["Value"] for t in top][::-1], color="#38a169")
        ax2.set_title("Top items by stock value")
    else:
        ax2.text(0.5, 0.5, "No stock yet", ha="center", va="center")
        ax2.set_axis_off()
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=app.content)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)

    ctk.CTkLabel(
        app.content,
        text=f"Total Sales: {round(sales, 2)}     "
             f"Total Purchases: {round(purch, 2)}",
        font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=6)
