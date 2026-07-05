# utils/backup.py
"""One-click backup: copy a company's .db file into a /backups folder."""
import os
import shutil
from datetime import datetime
from db.engine import company_path

BACKUP_DIR = os.path.join(os.getcwd(), "backups")


def backup_company(slug):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    src = company_path(slug)
    if not os.path.exists(src):
        raise FileNotFoundError("Company database not found yet.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"{slug}_{stamp}.db")
    shutil.copy2(src, dst)
    return dst