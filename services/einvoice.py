# services/einvoice.py
"""E-Invoice (IRP schema) + E-Way Bill JSON generation and QR-code PDF export
from existing Sales Invoices. Educational format, close to the real IRP schema.
"""
import json
import os

from db.engine import get_session
from db.models import Company, Voucher, VoucherItem, Item, Ledger

EINVOICE_DIR = "einvoice"


def _ensure_dir():
    os.makedirs(EINVOICE_DIR, exist_ok=True)


def _company(s):
    c = s.query(Company).first()
    if not c:
        raise ValueError("No company found. Set up your company first.")
    return c


def list_sales_invoices():
    """Return sales invoices as [{id, number, date, party, total}]."""
    s = get_session()
    try:
        pnames = {l.id: l.name for l in s.query(Ledger).all()}
        rows = (s.query(Voucher).filter(Voucher.vtype == "Sales")
                .order_by(Voucher.date.desc()).all())
        return [{"id": v.id, "number": v.number, "date": str(v.date),
                 "party": pnames.get(v.party_id, ""), "total": v.total}
                for v in rows]
    finally:
        s.close()


def validate(voucher_id):
    """Return a list of human-readable problems (empty list = OK)."""
    s = get_session()
    try:
        v = s.get(Voucher, voucher_id)
        if not v:
            return ["Invoice not found."]
        c = _company(s)
        problems = []
        if not (c.gstin or "").strip():
            problems.append("Company GSTIN is missing.")
        party = s.get(Ledger, v.party_id) if v.party_id else None
        if not party or not (party.gstin or "").strip():
            problems.append("Buyer GSTIN is missing.")
        items = s.query(VoucherItem).filter_by(voucher_id=v.id).all()
        if not items:
            problems.append("Invoice has no item lines.")
        imap = {i.id: i for i in s.query(Item).all()}
        for vi in items:
            it = imap.get(vi.item_id)
            if not it or not (it.hsn or "").strip():
                nm = it.name if it else vi.item_id
                problems.append(f"Item '{nm}' has no HSN code.")
        return problems
    finally:
        s.close()


def build_einvoice(voucher_id):
    """Build an IRP-schema e-invoice dict from a Sales Invoice."""
    s = get_session()
    try:
        v = s.get(Voucher, voucher_id)
        if not v:
            raise ValueError("Invoice not found.")
        c = _company(s)
        party = s.get(Ledger, v.party_id) if v.party_id else None
        imap = {i.id: i for i in s.query(Item).all()}
        items = s.query(VoucherItem).filter_by(voucher_id=v.id).all()

        item_list = []
        tot_taxable = tot_cgst = tot_sgst = tot_igst = tot_val = 0.0
        for idx, vi in enumerate(items, start=1):
            it = imap.get(vi.item_id)
            taxable = round((vi.qty or 0) * (vi.rate or 0), 2)
            line_val = round(taxable + (vi.cgst or 0) + (vi.sgst or 0)
                             + (vi.igst or 0), 2)
            tot_taxable += taxable
            tot_cgst += vi.cgst or 0
            tot_sgst += vi.sgst or 0
            tot_igst += vi.igst or 0
            tot_val += line_val
            item_list.append({
                "SlNo": str(idx),
                "PrdDesc": it.name if it else "",
                "HsnCd": (it.hsn if it else "") or "",
                "Qty": vi.qty or 0,
                "Unit": "NOS",
                "UnitPrice": vi.rate or 0,
                "TotAmt": taxable,
                "AssAmt": taxable,
                "GstRt": vi.gst_rate or 0,
                "CgstAmt": round(vi.cgst or 0, 2),
                "SgstAmt": round(vi.sgst or 0, 2),
                "IgstAmt": round(vi.igst or 0, 2),
                "TotItemVal": line_val,
            })

        doc = {
            "Version": "1.1",
            "TranDtls": {"TaxSch": "GST", "SupTyp": "B2B"},
            "DocDtls": {"Typ": "INV", "No": v.number,
                        "Dt": v.date.strftime("%d/%m/%Y")},
            "SellerDtls": {
                "Gstin": c.gstin or "",
                "LglNm": c.name,
                "Addr1": c.address or "",
                "Loc": c.state or "",
                "StCd": c.state_code or "",
            },
            "BuyerDtls": {
                "Gstin": (party.gstin if party else "") or "",
                "LglNm": party.name if party else "",
                "Pos": (party.state_code if party else "") or "",
                "Addr1": (party.address if party else "") or "",
                "Loc": (party.state if party else "") or "",
                "StCd": (party.state_code if party else "") or "",
            },
            "ItemList": item_list,
            "ValDtls": {
                "AssVal": round(tot_taxable, 2),
                "CgstVal": round(tot_cgst, 2),
                "SgstVal": round(tot_sgst, 2),
                "IgstVal": round(tot_igst, 2),
                "TotInvVal": round(tot_val, 2),
            },
        }
        return doc
    finally:
        s.close()


def build_ewaybill(voucher_id, distance_km, transport_mode="1",
                   vehicle_no=""):
    """Build an e-way bill dict. transport_mode 1=Road,2=Rail,3=Air,4=Ship."""
    doc = build_einvoice(voucher_id)
    return {
        "supplyType": "O",
        "subSupplyType": "1",
        "docType": "INV",
        "docNo": doc["DocDtls"]["No"],
        "docDate": doc["DocDtls"]["Dt"],
        "fromGstin": doc["SellerDtls"]["Gstin"],
        "fromStateCode": doc["SellerDtls"]["StCd"],
        "toGstin": doc["BuyerDtls"]["Gstin"],
        "toStateCode": doc["BuyerDtls"]["StCd"],
        "totInvValue": doc["ValDtls"]["TotInvVal"],
        "transMode": str(transport_mode),
        "transDistance": str(distance_km),
        "vehicleNo": vehicle_no,
        "itemList": doc["ItemList"],
    }


def save_json(doc, filename):
    _ensure_dir()
    path = os.path.join(EINVOICE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    return path


def export_einvoice(voucher_id):
    doc = build_einvoice(voucher_id)
    return save_json(doc, f"einvoice_{doc['DocDtls']['No'].replace('/', '_')}.json")


def export_ewaybill(voucher_id, distance_km, transport_mode="1",
                    vehicle_no=""):
    doc = build_ewaybill(voucher_id, distance_km, transport_mode, vehicle_no)
    return save_json(doc, f"ewaybill_{doc['docNo'].replace('/', '_')}.json")


def make_qr_pdf(voucher_id):
    """Write a small A5 PDF containing invoice header + a QR code of the
    e-invoice payload. Returns the file path.
    """
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.units import mm

    _ensure_dir()
    doc = build_einvoice(voucher_id)
    payload = json.dumps({
        "No": doc["DocDtls"]["No"], "Dt": doc["DocDtls"]["Dt"],
        "SellerGstin": doc["SellerDtls"]["Gstin"],
        "BuyerGstin": doc["BuyerDtls"]["Gstin"],
        "TotInvVal": doc["ValDtls"]["TotInvVal"],
    })
    path = os.path.join(
        EINVOICE_DIR, f"qr_{doc['DocDtls']['No'].replace('/', '_')}.pdf")
    cnv = canvas.Canvas(path, pagesize=A5)
    w, h = A5
    cnv.setFont("Helvetica-Bold", 14)
    cnv.drawString(20 * mm, h - 20 * mm, "E-Invoice (educational)")
    cnv.setFont("Helvetica", 10)
    cnv.drawString(20 * mm, h - 30 * mm, f"Invoice No: {doc['DocDtls']['No']}")
    cnv.drawString(20 * mm, h - 36 * mm, f"Date: {doc['DocDtls']['Dt']}")
    cnv.drawString(20 * mm, h - 42 * mm,
                   f"Seller GSTIN: {doc['SellerDtls']['Gstin']}")
    cnv.drawString(20 * mm, h - 48 * mm,
                   f"Buyer GSTIN: {doc['BuyerDtls']['Gstin']}")
    cnv.drawString(20 * mm, h - 54 * mm,
                   f"Total: {doc['ValDtls']['TotInvVal']}")
    widget = qr.QrCodeWidget(payload)
    b = widget.getBounds()
    size = 60 * mm
    d = Drawing(size, size,
                transform=[size / (b[2] - b[0]), 0, 0,
                           size / (b[3] - b[1]), 0, 0])
    d.add(widget)
    renderPDF.draw(d, cnv, 20 * mm, h - 130 * mm)
    cnv.showPage()
    cnv.save()
    return path