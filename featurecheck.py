# featurecheck.py -- lists public functions (with signatures) per module
import importlib
import inspect

MODULES = [
    "core.numbering", "core.posting", "core.gst", "core.stock",
    "services.masters", "services.vouchers", "services.trading",
    "services.reports", "services.outstanding", "services.gst_returns",
    "services.einvoice", "services.taxes", "services.manufacturing",
    "services.inventory_adv", "services.pricing", "services.costing",
    "services.banking", "services.bank", "services.security",
    "services.auth", "services.currency", "services.pos",
    "services.orders", "services.datatools", "services.importer",
    "services.adv_financials", "services.comms", "services.doctemplate",
]

for m in MODULES:
    try:
        mod = importlib.import_module(m)
    except Exception as e:
        print("[ERR] " + m + ": " + str(e))
        continue
    funcs = [(n, o) for n, o in inspect.getmembers(mod, inspect.isfunction)
             if getattr(o, "__module__", "") == mod.__name__
             and not n.startswith("_")]
    print("\n== " + m + "  (" + str(len(funcs)) + ") ==")
    for n, o in funcs:
        try:
            sig = str(inspect.signature(o))
        except Exception:
            sig = "()"
        print("   " + n + sig)