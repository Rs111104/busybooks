# services/upi.py -- UPI payment QR code
import os


def make_upi_qr(vpa, name, amount, outpath=None):
    try:
        import qrcode
    except Exception:
        return "LIB_MISSING"
    uri = ("upi://pay?pa=%s&pn=%s&am=%.2f&cu=INR"
           % (vpa, str(name).replace(" ", "%20"), float(amount or 0)))
    img = qrcode.make(uri)
    outpath = outpath or os.path.join(os.getcwd(), "output",
                                      "upi_qr.png")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    img.save(outpath)
    return outpath