# services/doctemplate.py
"""Invoice/document template designer. Stores layout choices in settings so
your printed invoices can reuse them.
"""
import json

from utils.settings import get_setting, set_setting

_KEY = "invoice_template"

_DEFAULT = {
    "header": "TAX INVOICE",
    "accent_color": "#1f6aa5",
    "show_logo": True,
    "show_gstin": True,
    "show_hsn": True,
    "show_bank_details": True,
    "signatory": "For {company}",
    "footer_note": "Thank you for your business!",
    "terms": "Goods once sold will not be taken back.\n"
             "Subject to local jurisdiction.",
}


def default_template():
    return dict(_DEFAULT)


def load_template():
    raw = get_setting(_KEY, "")
    if raw:
        try:
            merged = dict(_DEFAULT)
            merged.update(json.loads(raw))
            return merged
        except Exception:
            pass
    return dict(_DEFAULT)


def save_template(fields):
    data = dict(_DEFAULT)
    data.update(fields or {})
    set_setting(_KEY, json.dumps(data))
    return data


def preview_text(company="Demo Traders", t=None):
    if t is None:
        t = load_template()
    lines = [t["header"], "=" * max(4, len(t["header"])), company]
    if t.get("show_gstin"):
        lines.append("GSTIN: 29ABCDE1234F1Z5")
    lines += ["", "Bill To: Sample Customer", ""]
    if t.get("show_hsn"):
        head = "Item        HSN    Qty   Rate    Amount"
        row = "Widget      8471    2    100.00   200.00"
    else:
        head = "Item            Qty   Rate    Amount"
        row = "Widget           2    100.00   200.00"
    lines += [head, "-" * len(head), row, "", "Total: 200.00"]
    if t.get("show_bank_details"):
        lines += ["", "Bank: Sample Bank  A/c: 000123456  IFSC: SBIN0000001"]
    lines += ["", t.get("terms", ""), "",
              t.get("signatory", "").replace("{company}", company),
              "", t.get("footer_note", "")]
    return "\n".join(lines)