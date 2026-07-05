# services/company_admin.py
"""Create, list and switch companies. Each company is its own SQLite file
created + seeded on demand.
"""
from db.engine import open_company, list_companies
from db.seed import seed_company
from utils.settings import get_setting, set_setting


def all_companies():
    return sorted(list_companies())


def current_company():
    return get_setting("company", "Demo Traders")


def create_company(name, state="", state_code="", gstin=""):
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a company name.")
    if name in list_companies():
        raise ValueError("A company with that name already exists.")
    open_company(name)                       # creates the .db + tables
    seed_company(name, state=state, state_code=state_code, gstin=gstin)
    return name


def switch_company(name):
    if name not in list_companies():
        raise ValueError("That company does not exist.")
    set_setting("company", name)
    return name