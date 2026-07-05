# core/numbering.py
"""Voucher numbering.

A number is only consumed when the CALLER commits, so a rolled-back
voucher never burns a number (no gaps, no out-of-sync numbers).
"""
from db.models import NumberSeries

DEFAULT_PREFIXES = {
    "Sales": "INV/",
    "Purchase": "PUR/",
    "Payment": "PAY/",
    "Receipt": "RCP/",
    "Journal": "JRN/",
    "Contra": "CON/",
    "CreditNote": "CRN/",
    "DebitNote": "DBN/",
}


def _series(session, vtype):
    s = session.query(NumberSeries).filter_by(vtype=vtype).one_or_none()
    if s is None:
        s = NumberSeries(
            vtype=vtype,
            prefix=DEFAULT_PREFIXES.get(vtype, vtype[:3].upper() + "/"),
            next_no=1,
            width=4,
        )
        session.add(s)
        session.flush()
    return s


def format_number(series, n):
    return f"{series.prefix}{str(n).zfill(series.width or 4)}"


def peek_number(session, vtype):
    """Return the number that WOULD be assigned next, without consuming it."""
    s = _series(session, vtype)
    return format_number(s, s.next_no)


def next_number(session, vtype):
    """Reserve and return the next number in THIS session/transaction.

    Does NOT commit; the caller's single commit makes it permanent, and a
    rollback releases it.
    """
    s = _series(session, vtype)
    number = format_number(s, s.next_no)
    s.next_no = (s.next_no or 1) + 1
    session.flush()
    return number