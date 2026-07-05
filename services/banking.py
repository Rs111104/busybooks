# services/banking.py
"""Banking suite: import a bank statement (CSV), auto-match to vouchers, and
reconcile lines against the book balance.
"""
from datetime import date as _date, datetime

from db.engine import get_session
from db.models import Ledger, Voucher, VoucherEntry
from db.models_banking import BankStatementLine


def bank_ledgers():
    s = get_session()
    try:
        return [l.name for l in s.query(Ledger).order_by(Ledger.name).all()
                if "bank" in (l.name or "").lower()
                or "cash" in (l.name or "").lower()]
    finally:
        s.close()


def _parse_date(val):
    val = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return _date.today()


def import_statement_csv(bank_ledger_name, path):
    """CSV needs a date column, a description/narration column, and either an
    'amount' column (+in / -out) or separate 'debit'/'credit' columns.
    """
    import pandas as pd
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    s = get_session()
    try:
        bank = s.query(Ledger).filter_by(name=bank_ledger_name).first()
        if not bank:
            raise ValueError("Unknown bank ledger.")
        n = 0
        for _, row in df.iterrows():
            dt = _parse_date(row.get("date", ""))
            desc = str(row.get("description",
                               row.get("narration", "")) or "")
            ref = str(row.get("ref", row.get("reference", "")) or "")
            if "amount" in df.columns:
                amt = float(row.get("amount") or 0)
                dc = "Dr" if amt >= 0 else "Cr"
                amt = abs(amt)
            else:
                deb = float(row.get("debit") or 0)
                cre = float(row.get("credit") or 0)
                if deb >= cre:
                    amt, dc = deb, "Dr"
                else:
                    amt, dc = cre, "Cr"
            s.add(BankStatementLine(bank_ledger_id=bank.id, date=dt,
                                    description=desc, ref=ref, amount=amt,
                                    dc=dc, reconciled=0))
            n += 1
        s.commit()
        return n
    finally:
        s.close()


def list_lines(bank_ledger_name, only_unreconciled=False):
    s = get_session()
    try:
        bank = s.query(Ledger).filter_by(name=bank_ledger_name).first()
        if not bank:
            return []
        q = s.query(BankStatementLine).filter_by(bank_ledger_id=bank.id)
        if only_unreconciled:
            q = q.filter(BankStatementLine.reconciled == 0)
        return [{"id": r.id, "Date": str(r.date),
                 "Description": r.description, "Ref": r.ref,
                 "Amount": r.amount, "Dr/Cr": r.dc,
                 "Reconciled": "Yes" if r.reconciled else ""}
                for r in q.order_by(BankStatementLine.date,
                                    BankStatementLine.id).all()]
    finally:
        s.close()


def auto_match(bank_ledger_name):
    """Mark a line reconciled when a voucher entry on the same bank ledger has
    the same amount within +/- 3 days.
    """
    s = get_session()
    try:
        bank = s.query(Ledger).filter_by(name=bank_ledger_name).first()
        if not bank:
            raise ValueError("Unknown bank ledger.")
        entries = (s.query(VoucherEntry, Voucher)
                   .join(Voucher, VoucherEntry.voucher_id == Voucher.id)
                   .filter(VoucherEntry.ledger_id == bank.id).all())
        matched = 0
        lines = (s.query(BankStatementLine)
                 .filter_by(bank_ledger_id=bank.id, reconciled=0).all())
        for line in lines:
            want = round(line.amount or 0, 2)
            for entry, v in entries:
                book_amt = round((entry.debit or 0) + (entry.credit or 0), 2)
                same_amt = abs(book_amt - want) < 0.01
                close_date = (v.date and line.date and
                              abs((v.date - line.date).days) <= 3)
                if same_amt and close_date:
                    line.reconciled = 1
                    line.matched_voucher_id = v.id
                    matched += 1
                    break
        s.commit()
        return matched
    finally:
        s.close()


def set_reconciled(line_id, value):
    s = get_session()
    try:
        row = s.get(BankStatementLine, line_id)
        if row:
            row.reconciled = 1 if value else 0
            s.commit()
    finally:
        s.close()


def summary(bank_ledger_name):
    s = get_session()
    try:
        bank = s.query(Ledger).filter_by(name=bank_ledger_name).first()
        if not bank:
            return {}
        lines = s.query(BankStatementLine).filter_by(
            bank_ledger_id=bank.id).all()
        stmt_bal = sum((l.amount if l.dc == "Dr" else -l.amount)
                       for l in lines)
        book_bal = 0.0
        for e in s.query(VoucherEntry).filter_by(ledger_id=bank.id).all():
            book_bal += (e.debit or 0) - (e.credit or 0)
        unrec = sum(1 for l in lines if not l.reconciled)
        return {"Statement balance": round(stmt_bal, 2),
                "Book balance": round(book_bal, 2),
                "Difference": round(stmt_bal - book_bal, 2),
                "Unreconciled lines": unrec, "Total lines": len(lines)}
    finally:
        s.close()