# ui/analytics_screen.py
"""Analytics Dashboard with charts (matplotlib embedded in the window)."""
import datetime
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services import analytics


def show_analytics(app):
    app._clear()
    app._title("Analytics Dashboard")

    year = str(datetime.date.today().year)

    top = ctk.CTkFrame(app.content)
    top.pack(fill="x", pady=4)
    ctk.CTkLabel(top, text="Year:").grid(row=0, column=0, padx=4, pady=6)
    year_e = ctk.CTkEntry(top, width=100)
    year_e.insert(0, year)
    year_e.grid(row=0, column=1, padx=4)

    holder = ctk.CTkFrame(app.content)
    holder.pack(fill="both", expand=True)

    fig = Figure(figsize=(9, 6), dpi=100)
    canvas = FigureCanvasTkAgg(fig, master=holder)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def draw():
        fig.clear()
        yr = year_e.get() or year

        labels, values = analytics.sales_by_month(yr)
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.bar(labels, values, color="#1f6aa5")
        ax1.set_title(f"Monthly sales {yr}")
        ax1.set_xlabel("Month")

        inames, ivals = analytics.top_items()
        ax2 = fig.add_subplot(2, 2, 2)
        if inames:
            ax2.barh(inames[::-1], ivals[::-1], color="#2e7d32")
        ax2.set_title("Top items by value")

        recv, pay = analytics.receivables_payables()
        ax3 = fig.add_subplot(2, 1, 2)
        ax3.bar(["Receivables", "Payables"], [recv, pay],
                color=["#0b8043", "#b03030"])
        ax3.set_title("Receivables vs Payables")

        fig.tight_layout()
        canvas.draw()

    ctk.CTkButton(top, text="Refresh", command=draw).grid(
        row=0, column=2, padx=6)
    draw()