def show_inventory_adv(app):
    from services import inventory_adv
    from ui._auto_screen import render_service
    render_service(app, "Advanced Inventory", inventory_adv)