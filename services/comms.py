# services/comms.py
"""Communication center: message templates, mail-merge rendering with party
data, and a simulated 'send' that writes each message into an outbox folder
and records a log.
"""
import os
from datetime import datetime, date as _date

from db.engine import get_session
from db.models import Company, Ledger
from db.models_comm import MessageTemplate, MessageLog

OUTBOX_DIR = "outbox"


def _ensure_dir():
    os.makedirs(OUTBOX_DIR, exist_ok=True)


def list_templates():
    s = get_session()
    try:
        return [{"name": t.name, "channel": t.channel, "subject": t.subject,
                 "body": t.body} for t in
                s.query(MessageTemplate).order_by(MessageTemplate.name).all()]
    finally:
        s.close()


def save_template(name, channel, subject, body):
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a template name.")
    s = get_session()
    try:
        t = s.query(MessageTemplate).filter_by(name=name).first()
        if t:
            t.channel = channel
            t.subject = subject
            t.body = body
        else:
            s.add(MessageTemplate(name=name, channel=channel,
                                  subject=subject, body=body))
        s.commit()
    finally:
        s.close()


def delete_template(name):
    s = get_session()
    try:
        t = s.query(MessageTemplate).filter_by(name=name).first()
        if t:
            s.delete(t)
            s.commit()
    finally:
        s.close()


def party_contacts():
    s = get_session()
    try:
        rows = (s.query(Ledger).filter(Ledger.is_party == True)  # noqa: E712
                .order_by(Ledger.name).all())
        return [{"name": l.name, "phone": l.phone or "",
                 "email": l.email or ""} for l in rows]
    finally:
        s.close()


def _fields_for(s, party_name):
    company = s.query(Company).first()
    party = s.query(Ledger).filter_by(name=party_name).first()
    return {
        "{party}": party.name if party else party_name,
        "{phone}": (party.phone if party else "") or "",
        "{email}": (party.email if party else "") or "",
        "{gstin}": (party.gstin if party else "") or "",
        "{company}": company.name if company else "",
        "{date}": _date.today().strftime("%d/%m/%Y"),
    }


def render(text, party_name):
    s = get_session()
    try:
        out = text or ""
        for key, val in _fields_for(s, party_name).items():
            out = out.replace(key, str(val))
        return out
    finally:
        s.close()


def send(channel, party_name, subject, body):
    """Simulated send: writes the message to the outbox folder + logs it."""
    _ensure_dir()
    s = get_session()
    try:
        party = s.query(Ledger).filter_by(name=party_name).first()
        to_addr = ""
        if party:
            to_addr = (party.email if channel == "Email"
                       else party.phone) or ""
        subj = render(subject, party_name)
        text = render(body, party_name)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in party_name if c.isalnum() or c in " _-")
        fname = f"{channel}_{safe}_{stamp}.txt"
        path = os.path.join(OUTBOX_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Channel: {channel}\nTo: {to_addr}\nSubject: {subj}\n\n")
            f.write(text)
        s.add(MessageLog(party_id=party.id if party else None,
                         channel=channel, to_addr=to_addr, subject=subj,
                         body=text, status="Saved to outbox"))
        s.commit()
        return path
    finally:
        s.close()


def bulk_send(template_name, only_with_contact=True):
    tmpl = None
    for t in list_templates():
        if t["name"] == template_name:
            tmpl = t
            break
    if not tmpl:
        raise ValueError("Unknown template.")
    n = 0
    for c in party_contacts():
        if only_with_contact and not (c["phone"] or c["email"]):
            continue
        send(tmpl["channel"], c["name"], tmpl["subject"], tmpl["body"])
        n += 1
    return n


def log(limit=200):
    s = get_session()
    try:
        pmap = {l.id: l.name for l in s.query(Ledger).all()}
        rows = s.query(MessageLog).order_by(
            MessageLog.at.desc()).limit(limit).all()
        return [{"At": str(r.at), "Channel": r.channel,
                 "Party": pmap.get(r.party_id, ""), "To": r.to_addr,
                 "Subject": r.subject, "Status": r.status} for r in rows]
    finally:
        s.close()