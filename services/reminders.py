# services/reminders.py -- parties with outstanding receivable balances
from db.engine import get_session
from db.models import Ledger, VoucherEntry


def outstanding_parties():
    s = get_session()
    out = []
    parties = s.query(Ledger).filter(Ledger.is_party.is_(True)).all()
    for l in parties:
        entries = (s.query(VoucherEntry)
                   .filter(VoucherEntry.ledger_id == l.id).all())
        bal = sum((e.debit or 0) - (e.credit or 0) for e in entries)
        sign = 1 if (l.opening_dc or "Dr") == "Dr" else -1
        bal += (l.opening_balance or 0) * sign
        if round(bal, 2) > 0:
            out.append({
                "party": l.name,
                "phone": l.phone or "",
                "email": l.email or "",
                "due": round(bal, 2),
            })
    out.sort(key=lambda r: r["due"], reverse=True)
    return out