# services/taxes.py
"""TDS / TCS: manage sections, compute and record deductions/collections, and
report totals by section.
"""
from datetime import date as _date

from db.engine import get_session
from db.models import Ledger
from db.models_tax import TDSSection, TaxDeduction

_DEFAULT_SECTIONS = [
    ("194C", "Payment to contractors", 1.0, 30000.0, "TDS"),
    ("194J", "Professional / technical fees", 10.0, 30000.0, "TDS"),
    ("194H", "Commission or brokerage", 5.0, 15000.0, "TDS"),
    ("194I", "Rent", 10.0, 240000.0, "TDS"),
    ("194Q", "Purchase of goods", 0.1, 5000000.0, "TDS"),
    ("206C(1H)", "TCS on sale of goods", 0.1, 5000000.0, "TCS"),
]


def seed_sections():
    s = get_session()
    try:
        for code, name, rate, thr, kind in _DEFAULT_SECTIONS:
            if not s.query(TDSSection).filter_by(code=code).first():
                s.add(TDSSection(code=code, name=name, rate=rate,
                                 threshold=thr, kind=kind))
        s.commit()
    finally:
        s.close()


def list_sections(kind=None):
    s = get_session()
    try:
        q = s.query(TDSSection)
        if kind:
            q = q.filter(TDSSection.kind == kind)
        return [{"code": x.code, "name": x.name, "rate": x.rate,
                 "threshold": x.threshold, "kind": x.kind}
                for x in q.order_by(TDSSection.code).all()]
    finally:
        s.close()


def add_section(code, name, rate, threshold=0.0, kind="TDS"):
    code = (code or "").strip()
    if not code:
        raise ValueError("Enter a section code.")
    s = get_session()
    try:
        row = s.query(TDSSection).filter_by(code=code).first()
        if row:
            row.name = name
            row.rate = float(rate or 0)
            row.threshold = float(threshold or 0)
            row.kind = kind
        else:
            s.add(TDSSection(code=code, name=name, rate=float(rate or 0),
                             threshold=float(threshold or 0), kind=kind))
        s.commit()
    finally:
        s.close()


def party_names():
    s = get_session()
    try:
        rows = (s.query(Ledger).filter(Ledger.is_party == True)  # noqa: E712
                .order_by(Ledger.name).all())
        return [l.name for l in rows]
    finally:
        s.close()


def compute(base_amount, rate):
    return round(float(base_amount or 0) * float(rate or 0) / 100.0, 2)


def record(kind, section_code, party_name, base_amount, rate=None,
           vdate=None, narration=None):
    s = get_session()
    try:
        party = s.query(Ledger).filter_by(name=party_name).first()
        sec = s.query(TDSSection).filter_by(code=section_code).first()
        if rate is None:
            rate = sec.rate if sec else 0.0
        tax = round(float(base_amount or 0) * float(rate or 0) / 100.0, 2)
        row = TaxDeduction(kind=kind, section_code=section_code,
                           party_id=party.id if party else None,
                           base_amount=float(base_amount or 0),
                           rate=float(rate or 0), tax_amount=tax,
                           date=vdate or _date.today(), narration=narration)
        s.add(row)
        s.commit()
        return tax
    finally:
        s.close()


def list_deductions(kind=None):
    s = get_session()
    try:
        pmap = {l.id: l.name for l in s.query(Ledger).all()}
        q = s.query(TaxDeduction)
        if kind:
            q = q.filter(TaxDeduction.kind == kind)
        return [{"Date": str(r.date), "Kind": r.kind,
                 "Section": r.section_code, "Party": pmap.get(r.party_id, ""),
                 "Base": r.base_amount, "Rate": r.rate, "Tax": r.tax_amount}
                for r in q.order_by(TaxDeduction.date, TaxDeduction.id).all()]
    finally:
        s.close()


def report(kind=None):
    """Totals grouped by (kind, section code)."""
    s = get_session()
    try:
        q = s.query(TaxDeduction)
        if kind:
            q = q.filter(TaxDeduction.kind == kind)
        totals = {}
        for r in q.all():
            key = (r.kind, r.section_code)
            agg = totals.setdefault(key, {"base": 0.0, "tax": 0.0})
            agg["base"] += r.base_amount or 0
            agg["tax"] += r.tax_amount or 0
        out = []
        for (k, code), agg in sorted(totals.items()):
            out.append({"Kind": k, "Section": code,
                        "Base total": round(agg["base"], 2),
                        "Tax total": round(agg["tax"], 2)})
        return out
    finally:
        s.close()