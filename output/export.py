# output/export.py
"""Export any report (headers + list of dict rows) to an .xlsx file."""
import os
from datetime import datetime
import pandas as pd

OUT_DIR = os.path.join(os.getcwd(), "exports")


def rows_to_excel(name, headers, rows):
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.DataFrame([[r.get(h, "") for h in headers] for r in rows],
                      columns=headers)
    safe = "".join(c for c in name if c.isalnum() or c in " _-").strip() \
        or "report"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUT_DIR, f"{safe}_{stamp}.xlsx")
    df.to_excel(path, index=False)   # uses openpyxl automatically
    return path