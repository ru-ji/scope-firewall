"""Contract check: runs every rule of scope.json (the executable SCOPE.md) against the app and derives the verdict.

Usage:
  contract.py check [target]                  all rules; exit 1 if any check fails
  contract.py regress <base app.py> <head app.py>   exit 1 if a rule passing on base fails on head
  contract.py verdict <rule-id|none> [target]
      rule violated -> defect, rule holds -> usage, no rule (none) -> out_of_scope
target: --local (default) drives the app's own HTTP handler in-process, with no network, so it works inside
        any agent sandbox; --local=<path> does the same for another app file (the tests use a frozen copy of
        the shipped app); or a base URL (e.g. http://localhost:8080) for a real HTTP run (used by CI).
"""
import importlib.util, io, json, os, sys, urllib.error, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SCOPE_FILE = os.environ.get("SCOPE_FILE") or os.path.join(ROOT, "scope.json")  # tests point it at a frozen contract
SCOPE = json.load(open(SCOPE_FILE))
RULES = {r["id"]: r for r in SCOPE["rules"]}
# (rule, check name, request body, expected status, expected total or None, exact response fields,
#  response fields that must be present, request path)
CHECKS = [(r["id"], c["name"], c["body"], c["status"], c.get("total"), c.get("fields", {}), c.get("present", []),
           c.get("path") or SCOPE["endpoint"]) for r in SCOPE["rules"] for c in r["checks"]]


class _Sock:
    """Just enough of a socket for http.server's StreamRequestHandler."""
    def __init__(self, raw):
        self.inp, self.out = io.BytesIO(raw), io.BytesIO()
    def makefile(self, mode, *a, **k):
        return self.inp if "r" in mode else self.out
    def sendall(self, b):
        self.out.write(b)
    def settimeout(self, t):
        pass


_handlers = {}


def _post_local(body, app=None, path=None):
    app = os.path.join(ROOT, app or SCOPE["app"])
    if not os.path.exists(app):
        return 0, "app not built yet"
    if app not in _handlers:
        spec = importlib.util.spec_from_file_location(f"scope_app_{len(_handlers)}", app)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _handlers[app] = type("Quiet", (mod.H,), {"log_message": lambda *a: None})
    data = json.dumps(body).encode()
    raw = (f"POST {path or SCOPE['endpoint']} HTTP/1.1\r\nHost: local\r\nContent-Type: application/json\r\n"
           f"Content-Length: {len(data)}\r\n\r\n").encode() + data
    sock = _Sock(raw)
    _handlers[app](sock, ("local", 0), None)
    head, _, payload = sock.out.getvalue().partition(b"\r\n\r\n")
    return int(head.split()[1]), payload.decode()


def _post_http(base, body, path=None):
    req = urllib.request.Request(base.rstrip("/") + (path or SCOPE["endpoint"]), json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except OSError as e:
        return 0, f"unreachable: {e}"


def post(target, body, path=None):
    if target.startswith("--local"):
        return _post_local(body, target.partition("=")[2] or None, path)
    return _post_http(target, body, path)


def run(target="--local", rule=None):
    out = []
    for r, name, body, status, total, fields, present, path in CHECKS:
        if rule and r != rule:
            continue
        code, raw = post(target, body, path)
        try:
            obj = json.loads(raw)
            obj = obj if isinstance(obj, dict) else {}
        except ValueError:
            obj = {}
        got = obj.get("total")
        ok = (code == status and (total is None or (isinstance(got, (int, float)) and abs(got - total) < 1e-9))
              and all(obj.get(k) == v for k, v in fields.items()) and all(k in obj for k in present))
        out.append({"rule": r, "check": name, "request": body, "path": path,
                    "expected": {"status": status, "total": total, **fields, **({"present": present} if present else {})},
                    "observed": {"status": code, "body": raw}, "pass": ok})
    return out


def verdict(rule, target="--local"):
    if rule == "none":
        return {"rule": None, "verdict": "out_of_scope", "security": False,
                "evidence": "no SCOPE.md rule covers this request"}
    if rule not in RULES:
        raise SystemExit(f"unknown rule {rule!r}; known: {list(RULES)} or none")
    checks = run(target, rule)
    failed = [c for c in checks if not c["pass"]]
    return {"rule": rule, "rule_text": RULES[rule]["text"], "verdict": "defect" if failed else "usage",
            "security": bool(failed) and RULES[rule]["security"], "failed": failed,
            "passed": [c["check"] for c in checks if c["pass"]]}


def regress(base_app, head_app):
    """Regression gate: rules that pass on the base app must still pass on the head app."""
    base = {(c["rule"], c["check"]): c["pass"] for c in run("--local=" + base_app)}
    head = {(c["rule"], c["check"]): c["pass"] for c in run("--local=" + head_app)}
    regressions = sorted(f"{r} {n}" for (r, n), ok in base.items() if ok and not head.get((r, n), False))
    fixed = sorted(f"{r} {n}" for (r, n), ok in head.items() if ok and not base.get((r, n), True))
    still_open = sorted(f"{r} {n}" for (r, n), ok in head.items() if not ok)
    return {"regressions": regressions, "fixed": fixed, "still_open": still_open}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["check"]:
        res = run(*a[1:2])
        for c in res:
            print(f"{'PASS' if c['pass'] else 'FAIL'}  {c['rule']}  {c['check']}  -> {c['observed']['status']} {c['observed']['body']}")
        sys.exit(0 if all(c["pass"] for c in res) else 1)
    if a[:1] == ["regress"] and len(a) == 3:
        r = regress(a[1], a[2])
        print(f"fixed: {', '.join(r['fixed']) or 'nothing'}")
        print(f"still open (not this change's job): {', '.join(r['still_open']) or 'none'}")
        print(f"regressions: {', '.join(r['regressions']) or 'none'}")
        sys.exit(1 if r["regressions"] else 0)
    if a[:1] == ["verdict"] and len(a) >= 2:
        print(json.dumps(verdict(a[1], *a[2:3]), indent=1))
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
