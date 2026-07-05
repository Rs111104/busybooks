# services/gstin.py -- standalone GSTIN format + checksum validator
import re

_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_FORMAT = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def check_digit(first14):
    """Official GSTIN check-digit for the first 14 characters."""
    first14 = (first14 or "").upper()
    total = 0
    for i, ch in enumerate(first14[:14]):
        v = _CHARS.find(ch)
        if v < 0:
            return "?"
        factor = 2 if (i % 2) else 1
        prod = v * factor
        total += (prod // 36) + (prod % 36)
    return _CHARS[(36 - (total % 36)) % 36]


def is_valid(gstin):
    g = (gstin or "").strip().upper()
    if not _FORMAT.match(g):
        return False
    return g[14] == check_digit(g[:14])


def validate(gstin):
    """Return {ok, reason, [state_code]} for UI use."""
    g = (gstin or "").strip().upper()
    if not _FORMAT.match(g):
        return {"ok": False,
                "reason": "Bad format (need 15 chars: 2-digit state, "
                          "10-char PAN, entity, Z, check digit)"}
    if g[14] != check_digit(g[:14]):
        return {"ok": False,
                "reason": "Checksum mismatch (expected %s)"
                          % check_digit(g[:14])}
    return {"ok": True, "reason": "Valid GSTIN", "state_code": g[:2]}