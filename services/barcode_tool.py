# services/barcode_tool.py -- Code-128 barcodes per item
import os
from db.engine import get_session
from db.models import Item


def _code(it):
    return "%06d" % (it.id or 0)


def item_names():
    s = get_session()
    return [i.name for i in s.query(Item).order_by(Item.name).all()]


def generate(item_name, outdir=None):
    s = get_session()
    it = s.query(Item).filter(Item.name == item_name).first()
    if not it:
        return None
    try:
        import barcode
        from barcode.writer import ImageWriter
    except Exception:
        return "LIB_MISSING"
    outdir = outdir or os.path.join(os.getcwd(), "output", "barcodes")
    os.makedirs(outdir, exist_ok=True)
    code = _code(it)
    obj = barcode.get("code128", code, writer=ImageWriter())
    return obj.save(os.path.join(outdir, "item_%s" % code))


def generate_all(outdir=None):
    s = get_session()
    done = []
    for it in s.query(Item).all():
        p = generate(it.name, outdir)
        if p and p != "LIB_MISSING":
            done.append(p)
    return done