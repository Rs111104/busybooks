# services/invoice_pdf.py -- rich invoice PDF (barcode + UPI QR)
import os
from db.engine import get_session
from db.models import Voucher, Ledger, VoucherItem, Item, Company


def _company(s):
    return s.query(Company).first()


def sales_vouchers(limit=100):
    s = get_session()
    return [{"id": v.id, "number": v.number or "", "date": str(v.date),
             "total": round(v.total or 0, 2)}
            for v in (s.query(Voucher).filter(Voucher.vtype == "Sales")
                      .order_by(Voucher.id.desc()).limit(limit).all())]


def build(voucher_id, upi_vpa="", upi_name=""):
    s = get_session()
    v = s.get(Voucher, voucher_id)
    if not v:
        return {"ok": False, "msg": "Voucher not found"}
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except Exception:
        return {"ok": False, "msg": "Run: pip install reportlab"}
    co = _company(s)
    party = s.get(Ledger, v.party_id) if v.party_id else None
    items = s.query(VoucherItem).filter(
        VoucherItem.voucher_id == v.id).all()
    names = {i.id: i.name for i in s.query(Item).all()}
    outdir = os.path.join(os.getcwd(), "output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "invoice_%s.pdf" % (v.number or v.id))
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, (co.name if co else "Tax Invoice"))
    c.setFont("Helvetica", 9)
    if co:
        y -= 16
        c.drawString(40, y, "GSTIN: %s  State: %s"
                     % (co.gstin or "", co.state or ""))
    y -= 24
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "TAX INVOICE")
    c.setFont("Helvetica", 9)
    c.drawRightString(w - 40, y, "No: %s   Date: %s"
                      % (v.number or v.id, v.date))
    y -= 20
    c.drawString(40, y, "Bill To: %s" % (party.name if party else ""))
    if party and getattr(party, "gstin", ""):
        y -= 12
        c.drawString(40, y, "Party GSTIN: %s" % party.gstin)
    y -= 26
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, y, "Item")
    c.drawRightString(320, y, "Qty")
    c.drawRightString(390, y, "Rate")
    c.drawRightString(470, y, "Amount")
    c.drawRightString(w - 40, y, "Tax")
    c.line(40, y - 3, w - 40, y - 3)
    c.setFont("Helvetica", 9)
    for it in items:
        y -= 15
        tax = (it.cgst or 0) + (it.sgst or 0) + (it.igst or 0)
        c.drawString(40, y, str(names.get(it.item_id, "")))
        c.drawRightString(320, y, "%.2f" % (it.qty or 0))
        c.drawRightString(390, y, "%.2f" % (it.rate or 0))
        c.drawRightString(470, y, "%.2f" % (it.amount or 0))
        c.drawRightString(w - 40, y, "%.2f" % tax)
        if y < 120:
            c.showPage()
            y = h - 60
    y -= 6
    c.line(40, y, w - 40, y)
    y -= 16
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(w - 40, y, "Grand Total: %.2f" % (v.total or 0))
    try:
        import barcode
        from barcode.writer import ImageWriter
        from reportlab.lib.utils import ImageReader
        bpath = os.path.join(outdir, "barcodes")
        os.makedirs(bpath, exist_ok=True)
        code = "%08d" % (v.id or 0)
        obj = barcode.get("code128", code, writer=ImageWriter())
        saved = obj.save(os.path.join(bpath, "inv_%s" % code))
        c.drawImage(ImageReader(saved), 40, 60, width=140, height=40,
                    preserveAspectRatio=True, mask="auto")
    except Exception:
        pass
    if upi_vpa:
        try:
            import qrcode
            from reportlab.lib.utils import ImageReader
            uri = ("upi://pay?pa=%s&pn=%s&am=%.2f&cu=INR"
                   % (upi_vpa,
                      str(upi_name or (co.name if co else "")).replace(
                          " ", "%20"), float(v.total or 0)))
            qpath = os.path.join(outdir, "invoice_%s_upi.png"
                                 % (v.number or v.id))
            qrcode.make(uri).save(qpath)
            c.drawImage(ImageReader(qpath), w - 150, 50, width=90,
                        height=90, preserveAspectRatio=True,
                        mask="auto")
            c.setFont("Helvetica", 7)
            c.drawRightString(w - 55, 45, "Scan to pay (UPI)")
        except Exception:
            pass
    c.save()
    return {"ok": True, "path": path}