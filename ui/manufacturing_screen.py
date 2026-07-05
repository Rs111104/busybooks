def show_manufacturing(app):
    from services import manufacturing
    from ui._auto_screen import render_service
    render_service(app, "Manufacturing", manufacturing)