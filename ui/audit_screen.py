import customtkinter as ctk
from ui import theme


def show_audit(app):
    from ui.app import _make_sheet
    from db.engine import get_session
    from db.models import AuditLog
    app._clear()
    app._title("Audit Trail")
    s = get_session()
    rows = []
    try:
        for a in (s.query(AuditLog)
                  .order_by(AuditLog.id.desc()).limit(500).all()):
            rows.append([a.id, a.action, a.entity, a.entity_id,
                         a.detail, str(a.at)])
    except Exception as e:
        theme.h2(app.content, "No audit data yet: " + str(e)).pack(
            anchor="w")
        return
    theme.h2(app.content, "Recent activity (%d)" % len(rows)).pack(
        anchor="w", pady=(0, 6))
    _make_sheet(app.content, ["#", "Action", "Entity", "ID", "Detail",
                              "At"], rows)