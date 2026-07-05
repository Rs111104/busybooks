# tests/conftest.py
"""Shared pytest fixtures: an isolated in-memory DB + minimal masters."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, AccountGroup, Ledger, Item, Unit


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


@pytest.fixture()
def masters(session):
    sales_grp = AccountGroup(name="Sales Accounts", nature="Income")
    debtors = AccountGroup(name="Sundry Debtors", nature="Assets")
    duties = AccountGroup(name="Duties & Taxes", nature="Liabilities")
    session.add_all([sales_grp, debtors, duties])
    session.flush()

    party = Ledger(name="ACME Ltd", group_id=debtors.id,
                   opening_balance=0, opening_dc="Dr", is_party=True,
                   state_code="29")
    sales_ac = Ledger(name="Sales", group_id=sales_grp.id,
                      opening_balance=0, opening_dc="Cr")
    out_cgst = Ledger(name="Output CGST", group_id=duties.id,
                      opening_balance=0, opening_dc="Cr")
    out_sgst = Ledger(name="Output SGST", group_id=duties.id,
                      opening_balance=0, opening_dc="Cr")
    unit = Unit(name="Nos", decimals=0)
    session.add_all([party, sales_ac, out_cgst, out_sgst, unit])
    session.flush()

    widget = Item(name="Widget", unit_id=unit.id, hsn="8471",
                  gst_rate=18, sale_rate=100, purchase_rate=60,
                  opening_qty=0, opening_rate=0)
    session.add(widget)
    session.flush()
    return {
        "party": party, "sales": sales_ac, "cgst": out_cgst,
        "sgst": out_sgst, "widget": widget,
    }