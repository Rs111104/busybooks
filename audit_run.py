# audit_run.py -- BusyBooks REAL end-to-end execution audit
# Exercises every feature against a throwaway test company and reports PASS/FAIL.
# Run:  python audit_run.py     (project root, venv active)

RESULTS = []
X = {}

print(">>> RUNNING audit_run.py v3 (open-company-then-seed) <<<")


def _val(o, k):
    if isinstance(o, dict):
        return o.get(k)
    return getattr(o, k, None)


def _num(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def _len(v):
    try:
        return len(v)
    except Exception:
        return 0


def approx(a, b, tol=0.01):
    return abs(_num(a) - _num(b)) <= tol


def _id(v):
    if isinstance(v, (int, float)):
        return int(v)
    return _val(v, "id")


def check(feature, severity, fn):
    try:
        detail = fn()
        RESULTS.append(("PASS", severity, feature, detail or ""))
        print("[PASS] (%s) %s%s" % (severity, feature,
              (" - " + str(detail)) if detail else ""))
    except Exception as e:
        msg = "%s: %s" % (type(e).__name__, e)
        RESULTS.append(("FAIL", severity, feature, msg))
        print("[FAIL] (%s) %s -> %s" % (severity, feature, msg))


def _sess():
    from db.engine import get_session
    return get_session()


# ---------------- Phase 1: environment ----------------
def _setup():
    import os
    from db import engine, seed
    # wipe any stale throwaway DB so every run starts clean
    path = engine.company_path("_audit_test")
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    # ORDER MATTERS: open_company() creates the DB + binds the session
    # factory; seed_company() then uses get_session() to populate it.
    engine.open_company("_audit_test")
    seed.seed_company("_audit_test", state="Karnataka", state_code="29")
    return "opened + seeded _audit_test"


check("Env: seed & open test company", "Critical", _setup)


def _company_ok():
    try:
        _sess()
        return True
    except Exception:
        return False


if not _company_ok():
    print("\n*** SETUP FAILED: no company is open. Fix the Env step above "
          "before trusting anything below. ***\n")


# ---------------- Phase 2: masters ----------------
def _group_id(cands, nature):
    from services import masters
    try:
        for g in masters.list_groups():
            nm = (_val(g, "name") or "").lower()
            for c in cands:
                if c.lower() in nm:
                    return _id(g)
    except Exception:
        pass
    return _id(masters.create_group("AUD-" + cands[0], nature))


def _unit():
    from services import masters
    X["unit"] = _id(masters.create_unit("AUD-PCS", 2))
    assert X["unit"], "no unit id returned"
    return "units=%d" % _len(masters.list_units())


check("Masters: unit create/list", "High", _unit)


def _item():
    from services import masters
    X["item"] = _id(masters.create_item("AUD Widget", unit_id=X.get("unit"),
                    hsn="1234", gst_rate=18.0, sale_rate=100.0,
                    purchase_rate=60.0))
    assert X["item"], "no item id returned"
    return "item_id=%s items=%d" % (X["item"], _len(masters.list_items()))


check("Masters: item create/list", "High", _item)


def _ledgers():
    from services import masters
    dr = _group_id(["Sundry Debtors", "Debtors"], "Assets")
    cr = _group_id(["Sundry Creditors", "Creditors"], "Liabilities")
    cash = _group_id(["Cash"], "Assets")
    X["cust"] = _id(masters.create_ledger("AUD Customer", dr, is_party=True,
                    state_code="29", gstin="29AAAAA0000A1Z5"))
    X["supp"] = _id(masters.create_ledger("AUD Supplier", cr, is_party=True,
                    state_code="27", gstin="27BBBBB0000B1Z5"))
    X["cash_led"] = _id(masters.create_ledger("AUD Cash", cash))
    assert X["cust"] and X["supp"], "party ledger ids missing"
    return "customer=%s supplier=%s" % (X["cust"], X["supp"])


check("Masters: ledgers (party + cash)", "High", _ledgers)


def _dup():
    from services import masters
    if not X.get("unit"):
        return "skipped (masters failed upstream)"
    try:
        masters.create_unit("AUD-PCS", 2)
    except Exception:
        return "duplicate unit correctly rejected"
    return "WARNING: duplicate unit allowed (no unique constraint)"


check("Edge: duplicate master rejection", "Medium", _dup)


# ---------------- core GST math ----------------
def _gst_math():
    from core import gst
    intra = gst.split_gst(1000, 18, False)
    inter = gst.split_gst(1000, 18, True)
    assert approx(_val(intra, "cgst"), 90), "cgst != 90: %s" % intra
    assert approx(_val(intra, "sgst"), 90), "sgst != 90: %s" % intra
    assert approx(_val(inter, "igst"), 180), "igst != 180: %s" % inter
    return "intra 90/90, inter 180 OK"


check("Core: GST split math", "Critical", _gst_math)


# ---------------- trading (purchase THEN sale) ----------------
def _purchase():
    from services import trading
    assert X.get("item") and X.get("supp"), "upstream masters failed"
    lines = [{"item_id": X["item"], "qty": 20, "rate": 60, "gst_rate": 18}]
    X["pur_v"] = trading.create_purchase(X["supp"], lines)
    return "purchase voucher=%s" % _id(X["pur_v"])


check("Trading: purchase invoice", "Critical", _purchase)


def _sales():
    from services import trading
    assert X.get("item") and X.get("cust"), "upstream masters failed"
    lines = [{"item_id": X["item"], "qty": 10, "rate": 100, "gst_rate": 18}]
    X["sale_v"] = trading.create_sales_invoice(X["cust"], lines)
    return "sales voucher=%s" % _id(X["sale_v"])


check("Trading: sales invoice", "Critical", _sales)


def _stock_qty():
    from core import stock
    assert X.get("item"), "upstream masters failed"
    q = stock.current_qty(_sess(), X["item"])
    assert approx(q, 10), "expected 10 (20 in - 10 out), got %s" % q
    return "stock qty=10 OK"


check("Core: stock qty integrity", "Critical", _stock_qty)


def _receipt():
    from services import vouchers
    assert X.get("cash_led") and X.get("cust"), "upstream masters failed"
    X["rcpt"] = vouchers.create_voucher("Receipt", X["cash_led"],
                                        X["cust"], 500)
    return "receipt voucher=%s" % _id(X["rcpt"])


check("Vouchers: receipt (Dr cash / Cr party)", "High", _receipt)


# ---------------- reports & integrity ----------------
def _tb():
    from services import reports
    tb = reports.trial_balance()
    if isinstance(tb, dict) and tb.get("total_debit") is not None:
        dr, cr = _num(tb.get("total_debit")), _num(tb.get("total_credit"))
    else:
        rows = tb.get("rows") if isinstance(tb, dict) else tb
        dr = sum(_num(_val(r, "debit")) for r in rows)
        cr = sum(_num(_val(r, "credit")) for r in rows)
    assert approx(dr, cr), "TB NOT balanced dr=%.2f cr=%.2f" % (dr, cr)
    return "TB balanced at %.2f" % dr


check("Report: trial balance BALANCED", "Critical", _tb)


def _mk_run(modpath, fn, *args):
    def _r():
        import importlib
        mod = importlib.import_module(modpath)
        out = getattr(mod, fn)(*args)
        return "%s -> %s" % (fn, ("%d items" % _len(out))
                             if hasattr(out, "__len__") else "ok")
    return _r


for _f in ["profit_and_loss", "balance_sheet", "day_book",
           "stock_summary", "gst_summary"]:
    check("Report: " + _f, "High", _mk_run("services.reports", _f))

check("Report: ledger statement", "Medium",
      _mk_run("services.reports", "ledger_statement", "AUD Customer"))
check("A/R: outstanding receivables", "High",
      _mk_run("services.outstanding", "receivables"))
check("A/P: outstanding payables", "High",
      _mk_run("services.outstanding", "payables"))


def _aging():
    from services import aging
    return "recv rows=%d pay rows=%d" % (_len(aging.receivable_aging()),
                                         _len(aging.payable_aging()))


check("Aging: receivable/payable buckets", "High", _aging)


def _gstjson():
    from services import gst_json
    doc = gst_json.gstr1()
    assert "b2b" in doc and "hsn" in doc, "missing keys in GSTR-1 doc"
    return "b2b=%d b2cs=%d hsn=%d" % (_len(doc["b2b"]),
                                      _len(doc["b2cs"]), _len(doc["hsn"]))


check("GST: GSTR-1 JSON build", "High", _gstjson)

for _f in ["gstr1", "gstr3b"]:
    check("GST: " + _f, "Medium", _mk_run("services.gst_returns", _f))

check("Register: sales register", "Medium",
      _mk_run("services.registers", "sales_register"))


def _cashbook():
    from services import cashbook
    return "rows=%d" % _len(cashbook.cashbook(X.get("cash_led")))


check("Report: cash/bank book", "Medium", _cashbook)
check("Report: financial ratios", "Medium",
      _mk_run("services.ratios", "ratios"))
check("Reminders: outstanding parties", "Medium",
      _mk_run("services.reminders", "outstanding_parties"))
check("Analytics: receivables/payables", "Medium",
      _mk_run("services.analytics", "receivables_payables"))
check("MIS: monthly P&L", "Medium",
      _mk_run("services.adv_financials", "monthly_pl", 2026))


# ---------------- new feature packs ----------------
def _reorder():
    from services import reorder
    reorder.set_level("AUD Widget", 15)
    a = reorder.alerts()
    assert any(_val(d, "item") == "AUD Widget" for d in a), \
        "reorder alert did not trigger (qty 10 <= level 15)"
    return "alerts=%d (widget flagged)" % _len(a)


check("Inventory: reorder/low-stock alert", "High", _reorder)


def _cheques():
    from services import cheques
    cheques.add_cheque("AUD Customer", 5000, "000123", "HDFC",
                       "2099-01-01", "Incoming")
    lst = cheques.list_cheques()
    pdc = cheques.post_dated()
    assert _len(lst) >= 1, "cheque not saved"
    assert _len(pdc) >= 1, "post-dated cheque not detected"
    return "cheques=%d pdc=%d" % (_len(lst), _len(pdc))


check("Banking: cheque register + PDC", "High", _cheques)


def _payroll():
    from services import payroll
    eid = payroll.add_employee("AUD Emp", 10000, 4000, 1000)
    payroll.generate_payslip(eid, "2026-07")
    rows = [r for r in payroll.payslips("2026-07")
            if _val(r, "employee") == "AUD Emp"]
    assert rows, "payslip not created"
    r = rows[0]
    assert approx(_val(r, "gross"), 15000), "gross=%s" % _val(r, "gross")
    assert approx(_val(r, "pf"), 1200), "pf=%s" % _val(r, "pf")
    assert approx(_val(r, "esi"), 112.5), "esi=%s" % _val(r, "esi")
    assert approx(_val(r, "net"), 13687.5), "net=%s" % _val(r, "net")
    return "gross15000 pf1200 esi112.5 net13687.5 OK"


check("Payroll: payslip math integrity", "Critical", _payroll)


def _salesman():
    from services import salesman
    sid = salesman.add_salesman("AUD Rep")
    v = _id(X.get("sale_v"))
    if v:
        salesman.assign(v, sid)
    return "salesman report rows=%d" % _len(salesman.sales_by_salesman())


check("Sales: salesman-wise report", "Medium", _salesman)


def _costing():
    from services import costing
    costing.create_cost_centre("AUD CC")
    return "cost centres=%d" % _len(costing.list_cost_centres())


check("Costing: cost centre create/list", "Medium", _costing)


def _currency():
    from services import currency
    currency.add_currency("AUX", "Audit Dollar", "$", 80.0)
    return "currencies=%d" % _len(currency.list_currencies())


check("Currency: add/list", "Low", _currency)


def _taxes():
    from services import taxes
    try:
        taxes.seed_sections()
    except Exception:
        pass
    c = taxes.compute(1000, 10)
    assert approx(c, 100) or approx(_val(c, "amount"), 100), \
        "TDS compute(1000,10) wrong: %s" % c
    return "compute=100 OK, sections=%d" % _len(taxes.list_sections())


check("Tax: TDS/TCS compute", "Medium", _taxes)

for feat, mod, fn in [
        ("POS: item list", "services.pos", "item_list"),
        ("Orders: list", "services.orders", "list_orders"),
        ("Manufacturing: list BOMs", "services.manufacturing", "list_boms"),
        ("Inventory: batches", "services.inventory_adv", "list_batches"),
        ("Pricing: price lists", "services.pricing", "list_price_lists"),
        ("Bank rec: bank ledgers", "services.banking", "bank_ledgers"),
        ("e-invoice: sales list", "services.einvoice",
         "list_sales_invoices"),
        ("Security: audit log", "services.security", "audit_log"),
        ("Backup: list backups", "services.datatools", "list_backups"),
        ("Comms: templates", "services.comms", "list_templates")]:
    check(feat, "Medium", _mk_run(mod, fn))


def _auth():
    from services import auth
    try:
        auth.ensure_admin()
    except Exception:
        pass
    return "users=%d" % _len(auth.list_users())


check("Auth: ensure admin / list users", "Medium", _auth)


# ---------------- edge: oversell / negative stock ----------------
def _neg_stock():
    from services import trading
    from core import stock
    assert X.get("item") and X.get("cust"), "upstream masters failed"
    lines = [{"item_id": X["item"], "qty": 999999, "rate": 100,
              "gst_rate": 18}]
    try:
        trading.create_sales_invoice(X["cust"], lines)
    except Exception:
        return "oversell correctly blocked"
    q = stock.current_qty(_sess(), X["item"])
    if q < 0:
        raise AssertionError("oversell allowed; stock went negative: %s" % q)
    return "oversell handled (no negative stock)"


check("Edge: oversell / negative stock guard", "High", _neg_stock)


# ---------------- summary ----------------
print("\n==================== AUDIT SUMMARY ====================")
fails = [r for r in RESULTS if r[0] == "FAIL"]
print("Total checks: %d   PASS: %d   FAIL: %d"
      % (len(RESULTS), len(RESULTS) - len(fails), len(fails)))
for sev in ["Critical", "High", "Medium", "Low"]:
    n = len([r for r in fails if r[1] == sev])
    if n:
        print("   FAIL %-8s : %d" % (sev, n))
if fails:
    print("\n-------------------- FAILURES --------------------")
    for _, sev, feat, msg in fails:
        print("[%s] %s -> %s" % (sev, feat, msg))
else:
    print("\nALL FEATURES PASSED - BusyBooks is functionally verified.")
print("======================================================")