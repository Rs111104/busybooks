# output/pdf.py
"""Generate a professional PDF for any voucher/invoice number."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer)

from db.engine import get_session
from db.models import Voucher, VoucherItem, Item, Company, Ledger

OUT_DIR = os.path.join(os.getcwd(), "invoices")


def invoice_pdf(number):
    s = get_session()
    try:
        v = s.query(Voucher).filter_by(number=number).one_or_none()
        if not v:
            raise ValueError(f"No voucher found with number '{number}'.")
        company = s.query(Company).first()
        party = s.get(Ledger, v.party_id) if v.party_id else None
        item_names = {it.id: it.name for it in s.query(Item).all()}
        lines = s.query(VoucherItem).filter_by(voucher_id=v.id).all()
        data_rows = [[item_names.get(li.item_id, "?"), li.qty, li.rate,
                      li.amount, li.gst_rate,
                      round(li.cgst + li.sgst + li.igst, 2)] for li in lines]
        vtype, total, vdate = v.vtype, v.total, str(v.date)
        narration = v.narration or ""
        cname = company.name if company else "Company"
        cgstin = company.gstin if company else ""
        pname = party.name if party else ""
        pgstin = party.gstin if party else ""
    finally:
        s.close()

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{number.replace('/', '_')}.pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18 * mm)
    story = [Paragraph(f"<b>{cname}</b>", styles["Title"])]
    if cgstin:
        story.append(Paragraph(f"GSTIN: {cgstin}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>{vtype} {number}</b> &nbsp;&nbsp; "
                           f"Date: {vdate}", styles["Heading2"]))
    party_line = f"Party: {pname}"
    if pgstin:
        party_line += f" &nbsp; GSTIN: {pgstin}"
    story.append(Paragraph(party_line, styles["Normal"]))
    story.append(Spacer(1, 10))

    table_data = [["Item", "Qty", "Rate", "Amount", "GST %", "Tax"]] + data_rows
    t = Table(table_data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f0f4f8")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Grand Total: {total}</b>", styles["Heading2"]))
    if narration:
        story.append(Paragraph(f"Narration: {narration}", styles["Normal"]))
    doc.build(story)
    return path