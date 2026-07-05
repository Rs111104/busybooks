# services/security.py
"""User management, role permissions, and audit-log viewing. Reuses the User
and AuditLog tables from Day 1 / Day 10.
"""
import json

from db.engine import get_session
from db.models import User, AuditLog
from utils.settings import get_setting, set_setting

try:
    from utils.security import hash_password as _hash
except Exception:                       # fallback if named differently
    import hashlib

    def _hash(pw):
        return hashlib.sha256((pw or "").encode()).hexdigest()

ROLES = ["admin", "manager", "operator", "viewer"]
FEATURES = ["masters", "vouchers", "reports", "banking", "admin"]
_PERM_KEY = "role_permissions"

_DEFAULT_PERMS = {
    "admin": {f: True for f in FEATURES},
    "manager": {"masters": True, "vouchers": True, "reports": True,
                "banking": True, "admin": False},
    "operator": {"masters": True, "vouchers": True, "reports": True,
                 "banking": False, "admin": False},
    "viewer": {"masters": False, "vouchers": False, "reports": True,
               "banking": False, "admin": False},
}


def list_users():
    s = get_session()
    try:
        return [{"id": u.id, "Username": u.username, "Role": u.role,
                 "Active": "Yes" if u.active else ""}
                for u in s.query(User).order_by(User.username).all()]
    finally:
        s.close()


def create_user(username, password, role="operator"):
    username = (username or "").strip()
    if not username or not password:
        raise ValueError("Enter a username and password.")
    if role not in ROLES:
        raise ValueError("Unknown role.")
    s = get_session()
    try:
        if s.query(User).filter_by(username=username).first():
            raise ValueError("That username already exists.")
        s.add(User(username=username, password_hash=_hash(password),
                   role=role, active=True))
        s.commit()
    finally:
        s.close()


def set_role(user_id, role):
    if role not in ROLES:
        raise ValueError("Unknown role.")
    s = get_session()
    try:
        u = s.get(User, user_id)
        if u:
            u.role = role
            s.commit()
    finally:
        s.close()


def set_active(user_id, active):
    s = get_session()
    try:
        u = s.get(User, user_id)
        if u:
            u.active = bool(active)
            s.commit()
    finally:
        s.close()


def reset_password(user_id, new_password):
    if not new_password:
        raise ValueError("Enter a new password.")
    s = get_session()
    try:
        u = s.get(User, user_id)
        if u:
            u.password_hash = _hash(new_password)
            s.commit()
    finally:
        s.close()


def load_permissions():
    raw = get_setting(_PERM_KEY, "")
    if raw:
        try:
            data = json.loads(raw)
            for r in ROLES:
                data.setdefault(r, dict(_DEFAULT_PERMS[r]))
                for f in FEATURES:
                    data[r].setdefault(f, _DEFAULT_PERMS[r][f])
            return data
        except Exception:
            pass
    return {r: dict(v) for r, v in _DEFAULT_PERMS.items()}


def set_permission(role, feature, allowed):
    data = load_permissions()
    data.setdefault(role, {})[feature] = bool(allowed)
    set_setting(_PERM_KEY, json.dumps(data))


def can(role, feature):
    return load_permissions().get(role, {}).get(feature, False)


def audit_log(limit=200):
    s = get_session()
    try:
        umap = {u.id: u.username for u in s.query(User).all()}
        rows = (s.query(AuditLog).order_by(AuditLog.at.desc())
                .limit(limit).all())
        return [{"At": str(r.at), "User": umap.get(r.user_id, r.user_id),
                 "Action": r.action, "Entity": r.entity,
                 "Detail": r.detail} for r in rows]
    finally:
        s.close()