# ui/_auto_screen.py -- generic screen that adapts to a service module
import inspect
import customtkinter as ctk
from ui import theme


def render_service(app, title, module):
    from ui.app import _make_sheet
    app._clear()
    app._title(title)

    funcs = []
    for name in sorted(dir(module)):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if (inspect.isfunction(obj)
                and getattr(obj, "__module__", "") == module.__name__):
            funcs.append((name, obj))

    top = ctk.CTkFrame(app.content, fg_color="transparent")
    top.pack(fill="x", pady=(0, 8))
    holder = ctk.CTkFrame(app.content, fg_color="transparent")
    holder.pack(fill="both", expand=True)

    if not funcs:
        theme.muted(holder,
                    "This service has no actions to show yet.").pack(pady=20)
        return

    def run(fn):
        for w in holder.winfo_children():
            w.destroy()
        try:
            sig = inspect.signature(fn)
            required = [p for p in sig.parameters.values()
                        if p.default is inspect.Parameter.empty
                        and p.kind in (p.POSITIONAL_OR_KEYWORD,
                                       p.POSITIONAL_ONLY)]
        except (TypeError, ValueError):
            required = []
        if required:
            theme.muted(
                holder,
                "'{}' needs input ({}). Paste this service file to me and "
                "I'll build a proper form.".format(
                    fn.__name__, ", ".join(p.name for p in required))
            ).pack(pady=20)
            return
        try:
            result = fn()
        except Exception as e:
            theme.muted(holder, "Could not run {}: {}".format(
                fn.__name__, e)).pack(pady=20)
            return
        _render_result(holder, result, _make_sheet)

    for name, fn in funcs:
        theme.ghost_button(top, name.replace("_", " ").title(),
                           lambda f=fn: run(f)).pack(side="left",
                                                     padx=4, pady=2)
    theme.muted(holder, "Click an action above to run it.").pack(pady=20)


def _render_result(holder, result, _make_sheet):
    if isinstance(result, dict):
        rows = [[str(k), _s(v)] for k, v in result.items()]
        _make_sheet(holder, ["Key", "Value"], rows)
        return
    if isinstance(result, (list, tuple)):
        seq = list(result)
        if not seq:
            theme.muted(holder, "No records.").pack(pady=20)
            return
        first = seq[0]
        if isinstance(first, dict):
            headers = list(first.keys())
            rows = [[_s(r.get(h, "")) for h in headers]
                    for r in seq if isinstance(r, dict)]
            _make_sheet(holder, [str(h) for h in headers], rows)
            return
        if isinstance(first, (list, tuple)):
            width = max(len(x) for x in seq)
            headers = ["Col %d" % (i + 1) for i in range(width)]
            rows = [[_s(c) for c in x] for x in seq]
            _make_sheet(holder, headers, rows)
            return
        _make_sheet(holder, ["Value"], [[_s(x)] for x in seq])
        return
    theme.muted(holder, _s(result)).pack(pady=20)


def _s(v):
    try:
        if isinstance(v, float):
            return "{:,.2f}".format(v)
        return str(v)
    except Exception:
        return repr(v)