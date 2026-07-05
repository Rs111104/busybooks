# services/gstin.py -- GSTIN format + checksum validation
import re

_GSTIN_RE = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
_CODES = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _check_digit(first14):
    n = len(_CODES)
    factor = 2
    total = 0
    for ch in reversed(first14):
        code = _CODES.index(ch)
        addend = factor * code
        factor = 1 if factor == 2 else 2
        addend = (addend // n) + (addend % n)
        total += addend
    return _CODES[(n - (total % n)) % n]


def validate(gstin):
    g = (gstin or "").strip().upper()
    if len(g) != 15:
        return {"valid": False, "reason": "GSTIN must be 15 characters"}
    if not _GSTIN_RE.match(g):
        return {"valid": False, "reason": "Invalid GSTIN format"}
    expected = _check_digit(g[:14])
    if expected != g[14]:
        return {"valid": False,
                "reason": "Checksum failed (expected last char '%s')"
                % expected}
    return {"valid": True, "reason": "Valid GSTIN",
            "state_code": g[:2], "pan": g[2:12]}