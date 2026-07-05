# services/audit_hook.py -- automatic audit trail via SQLAlchemy events
from datetime import datetime
from sqlalchemy import event
from db import models as M
from db.models import AuditLog

CURRENT_USER_ID = None


def set_user(uid):
    global CURRENT_USER_ID
    CURRENT_USER_ID = uid


_AUDITED = ["Ledger", "Item", "Voucher", "AccountGroup", "Unit",
            "Godown", "Company", "User", "NumberSeries", "TaxRate",
            "ItemGroup"]


def _write(connection, action, target):
    try:
        detail = str(getattr(target, "name", "") or "")[:200]
        connection.execute(AuditLog.__table__.insert().values(
            user_id=CURRENT_USER_ID, action=action,
            entity=type(target).__name__,
            entity_id=getattr(target, "id", None),
            detail=detail, at=datetime.utcnow()))
    except Exception:
        pass


def _mk(action):
    def _h(mapper, connection, target):
        _write(connection, action, target)
    return _h


_installed = False


def install():
    global _installed
    if _installed:
        return
    for name in _AUDITED:
        cls = getattr(M, name, None)
        if cls is None:
            continue
        event.listen(cls, "after_insert", _mk("CREATE"))
        event.listen(cls, "after_update", _mk("UPDATE"))
        event.listen(cls, "after_delete", _mk("DELETE"))
    _installed = True


install()