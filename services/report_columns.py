# services/report_columns.py -- pick columns over existing services.reports
_NOARG = ["trial_balance", "profit_and_loss", "balance_sheet",
          "day_book", "stock_summary", "gst_summary"]


def available_reports():
    from services import reports
    return [n for n in _NOARG if hasattr(reports, n)]


def _normalize(result):
    """Return (columns, rows) with rows as a list of dicts, for any shape."""
    try:
        import pandas as pd
        if isinstance(result, pd.DataFrame):
            return ([str(c) for c in result.columns],
                    result.to_dict("records"))
    except Exception:
        pass
    if result is None:
        return [], []
    if isinstance(result, dict):
        return ["key", "value"], [{"key": str(k), "value": v}
                                  for k, v in result.items()]
    if isinstance(result, (list, tuple)):
        result = list(result)
        if not result:
            return [], []
        first = result[0]
        if isinstance(first, dict):
            cols = []
            for row in result:
                for k in row.keys():
                    if str(k) not in cols:
                        cols.append(str(k))
            return cols, [dict(r) for r in result]
        if isinstance(first, (list, tuple)):
            cols = ["col%d" % i for i in range(len(first))]
            return cols, [dict(zip(cols, r)) for r in result]
        return ["value"], [{"value": v} for v in result]
    return ["value"], [{"value": result}]


def fetch(report_name):
    from services import reports
    fn = getattr(reports, report_name, None)
    if not fn:
        return {"ok": False, "msg": "No such report: %s" % report_name}
    try:
        cols, rows = _normalize(fn())
        return {"ok": True, "columns": cols, "rows": rows}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def project(rows, columns):
    """Keep only the chosen columns, in order, as a list of lists."""
    columns = list(columns or [])
    return [[row.get(c, "") for c in columns] for row in (rows or [])]