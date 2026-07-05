# ui/theme.py
"""Central look-and-feel for BusyBooks.

Call theme.apply() once at startup, then use these helpers in any screen
for a consistent, modern UI.
"""
import customtkinter as ctk

# ---- palette (Busy-inspired: clean light UI, blue accents) ----
PRIMARY = "#1f6aa5"
PRIMARY_DARK = "#17537f"
ACCENT = "#0b8043"
DANGER = "#c0392b"
WARNING = "#e08600"
SIDEBAR_BG = "#0f2b46"
SIDEBAR_HOVER = "#1c3d5f"
CARD_BG = "#ffffff"
PAGE_BG = "#eef2f6"
BORDER = "#dfe6ee"
TEXT_MUTED = "#6b7785"

FONT = "Segoe UI"


def apply(mode="light", scale=1.0):
    """Set global appearance. Call BEFORE creating the main window."""
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")
    if scale and scale != 1.0:
        ctk.set_widget_scaling(scale)


def h1(parent, text):
    return ctk.CTkLabel(parent, text=text, font=(FONT, 22, "bold"))


def h2(parent, text):
    return ctk.CTkLabel(parent, text=text, font=(FONT, 15, "bold"))


def muted(parent, text):
    return ctk.CTkLabel(parent, text=text, text_color=TEXT_MUTED,
                        font=(FONT, 12))


def primary_button(parent, text, command, **kw):
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color=PRIMARY, hover_color=PRIMARY_DARK,
                         font=(FONT, 13, "bold"), height=36,
                         corner_radius=8, **kw)


def ghost_button(parent, text, command, **kw):
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color="transparent", hover_color=PAGE_BG,
                         text_color=PRIMARY, border_width=1,
                         border_color=PRIMARY, height=34,
                         corner_radius=8, **kw)


def danger_button(parent, text, command, **kw):
    return ctk.CTkButton(parent, text=text, command=command,
                         fg_color=DANGER, hover_color="#96271b",
                         font=(FONT, 13, "bold"), height=36,
                         corner_radius=8, **kw)


def card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                        border_width=1, border_color=BORDER, **kw)


def kpi_card(parent, title, value, accent=PRIMARY):
    c = card(parent)
    ctk.CTkLabel(c, text=title, text_color=TEXT_MUTED,
                 font=(FONT, 12)).pack(anchor="w", padx=16, pady=(14, 0))
    ctk.CTkLabel(c, text=value, text_color=accent,
                 font=(FONT, 26, "bold")).pack(anchor="w", padx=16,
                                               pady=(0, 14))
    return c


def style_sheet(sheet):
    """Apply consistent styling to a tksheet.Sheet (version-safe)."""
    try:
        sheet.set_options(
            header_bg=PRIMARY, header_fg="white",
            header_font=(FONT, 11, "bold"),
            font=(FONT, 11, "normal"),
            table_bg="white", table_grid_fg="#d8dfe6",
            selected_cells_border_color=PRIMARY,
            row_height=28,
        )
    except Exception:
        pass
    return sheet