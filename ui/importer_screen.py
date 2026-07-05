def show_importer(app):
    from services import importer
    from ui._auto_screen import render_service
    render_service(app, "Data Importer", importer)