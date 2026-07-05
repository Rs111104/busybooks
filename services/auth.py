# services/auth.py
"""User accounts, login and roles. A default admin/admin is created the
first time so you can always get in.
"""
from db.engine import get_session
from db.models import User, AuditLog
from utils.security import hash_password, verify_password


def ensure_admin():
    s = get_session()
    try:
        if s.query(User).count() == 0:
            s.add(User(username="admin",
                       password_hash=hash_password("admin"), role="admin"))
            s.commit()
    finally:
        s.close()


def login(username, password):
    s = get_session()
    try:
        u = s.query(User).filter_by(username=username, active=True) \
            .one_or_none()
        if u and verify_password(password, u.password_hash):
            s.add(AuditLog(user_id=u.id, action="LOGIN", entity="users",
                           entity_id=u.id, detail=f"{username} logged in"))
            s.commit()
            return {"id": u.id, "username": u.username, "role": u.role}
        return None
    finally:
        s.close()


def create_user(username, password, role="operator"):
    s = get_session()
    try:
        if s.query(User).filter_by(username=username).count():
            raise ValueError("That username already exists.")
        s.add(User(username=username, password_hash=hash_password(password),
                   role=role))
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def list_users():
    s = get_session()
    try:
        return [{"id": u.id, "username": u.username, "role": u.role,
                 "active": "Yes" if u.active else "No"}
                for u in s.query(User).order_by(User.username).all()]
    finally:
        s.close()


def recent_audit(limit=100):
    s = get_session()
    try:
        rows = s.query(AuditLog).order_by(AuditLog.at.desc()).limit(limit) \
            .all()
        return [{"When": str(a.at)[:19], "Action": a.action,
                 "Entity": a.entity, "Detail": a.detail or ""} for a in rows]
    finally:
        s.close()