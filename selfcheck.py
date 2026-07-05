# selfcheck.py  --  run from the project root:  python selfcheck.py
# Safe: it only imports files and checks screens. It does NOT change data.
import importlib
import importlib.util

MODULES = [
    # database layer
    "db.models", "db.engine", "db.seed",
    "db.models_orders", "db.models_inventory", "db.models_mfg",
    "db.models_pricing", "db.models_costing", "db.models_tax",
    "db.models_banking", "db.models_comm", "db.models_currency",
    # core logic
    "core.numbering", "core.posting", "core.gst", "core.stock",
    # services
    "services.masters", "services.vouchers", "services.trading",
    "services.reports", "services.auth", "services.voucher_admin",
    "services.company_admin", "services.gst_returns", "services.outstanding",
    "services.bank", "services.importer", "services.registers",
    "services.item_ledger", "services.cashbook", "services.reminders",
    "services.ratios", "services.orders", "services.inventory_adv",
    "services.manufacturing", "services.pricing", "services.einvoice",
    "services.taxes", "services.costing", "services.adv_financials",
    "services.banking", "services.security", "services.comms",
    "services.doctemplate", "services.currency", "services.pos",
    "services.datatools", "services.analytics",
    # output + utils
    "output.export", "output.pdf",
    "utils.security", "utils.backup", "utils.settings",
    # ui core
    "ui.theme", "ui.app", "ui.masters_screen",
]

# (module, function) menu items referenced by ui/app.py
SCREENS = [
    ("ui.vouchers_screen", "show_vouchers"),
    ("ui.pos_screen", "show_pos"),
    ("ui.orders_screen", "show_orders"),
    ("ui.manufacturing_screen", "show_manufacturing"),
    ("ui.pricing_screen", "show_pricing"),
    ("ui.inventory_adv_screen", "show_inventory_adv"),
    ("ui.item_ledger_screen", "show_item_ledger"),
    ("ui.reports_screen", "show_reports"),
    ("ui.adv_financials_screen", "show_adv_financials"),
    ("ui.outstanding_screen", "show_outstanding"),
    ("ui.registers_screen", "show_registers"),
    ("ui.cashbook_screen", "show_cashbook"),
    ("ui.ratios_screen", "show_ratios"),
    ("ui.analytics_screen", "show_analytics"),
    ("ui.reminders_screen", "show_reminders"),
    ("ui.gst_returns_screen", "show_gst_returns"),
    ("ui.taxes_screen", "show_taxes"),
    ("ui.einvoice_screen", "show_einvoice"),
    ("ui.costing_screen", "show_costing"),
    ("ui.banking_screen", "show_banking"),
    ("ui.bank_screen", "show_bank"),
    ("ui.importer_screen", "show_importer"),
    ("ui.currency_screen", "show_currency"),
    ("ui.designer_screen", "show_designer"),
    ("ui.comms_screen", "show_comms"),
    ("ui.datatools_screen", "show_datatools"),
    ("ui.security_screen", "show_security"),
    ("ui.admin_screen", "show_admin"),
]


def status(modname):
    try:
        spec = importlib.util.find_spec(modname)
    except Exception as e:
        return ("BROKEN", "find_spec: " + str(e))
    if spec is None:
        return ("MISSING", "no such file")
    try:
        importlib.import_module(modname)
        return ("OK", "")
    except Exception as e:
        return ("BROKEN", type(e).__name__ + ": " + str(e))


def main():
    ok = miss = broke = 0
    broken_lines = []
    missing_lines = []
    for m in MODULES:
        st, why = status(m)
        if st == "OK":
            ok += 1
        elif st == "MISSING":
            miss += 1
            missing_lines.append("  [MISSING] " + m)
        else:
            broke += 1
            broken_lines.append("  [BROKEN ] " + m + " -> " + why)

    print("=" * 62)
    print(" MODULE IMPORT REPORT")
    print("=" * 62)
    print(" OK: %d   MISSING: %d   BROKEN: %d   (of %d)"
          % (ok, miss, broke, len(MODULES)))
    if missing_lines:
        print("\n -- MISSING FILES --")
        print("\n".join(missing_lines))
    if broken_lines:
        print("\n -- BROKEN (file exists but errors on import) --")
        print("\n".join(broken_lines))

    print("\n" + "=" * 62)
    print(" SCREEN CHECK (menu items in ui/app.py)")
    print("=" * 62)
    resolved = 0
    not_res = []
    for mod, func in SCREENS:
        try:
            spec = importlib.util.find_spec(mod)
        except Exception as e:
            not_res.append("  [X] %s.%s -> find_spec: %s" % (mod, func, e))
            continue
        if spec is None:
            not_res.append("  [X] %s.%s -> file missing" % (mod, func))
            continue
        try:
            mm = importlib.import_module(mod)
            if callable(getattr(mm, func, None)):
                resolved += 1
            else:
                not_res.append("  [X] %s.%s -> function not found"
                               % (mod, func))
        except Exception as e:
            not_res.append("  [X] %s.%s -> %s: %s"
                           % (mod, func, type(e).__name__, e))
    print(" RESOLVED: %d / %d" % (resolved, len(SCREENS)))
    if not_res:
        print("\n -- NOT RESOLVED (show as 'More' / 'not built yet') --")
        print("\n".join(not_res))

    print("\nDONE. Copy everything above this line and send it to me.")


if __name__ == "__main__":
    main()