# probe.py  --  run: python probe.py   (paste ALL output)
import traceback

from db import engine
print("=== engine members ===")
print(sorted(x for x in dir(engine) if not x.startswith("_")))

try:
    from db import seed
    print("=== seed members ===")
    print(sorted(x for x in dir(seed) if not x.startswith("_")))
except Exception:
    print("--- import seed failed ---")
    traceback.print_exc()

print("\n=== try: engine.open_company('_probe') ===")
try:
    engine.open_company("_probe")
    print(">>> open_company returned OK")
except Exception:
    traceback.print_exc()

print("\n=== try: get_session() after open ===")
try:
    from db.engine import get_session
    print(">>> get_session OK:", type(get_session()))
except Exception:
    traceback.print_exc()

print("\n=== existing companies ===")
try:
    print(engine.list_companies())
except Exception:
    traceback.print_exc()