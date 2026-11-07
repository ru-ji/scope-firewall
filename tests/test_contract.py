"""The contract checker must flag the shipped app's real defects (frozen in tests/fixtures) AND pass a correct implementation."""
import os
os.environ["SCOPE_FILE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "scope_demo.json")  # tests judge the frozen demo contract, whatever the live scope is
import json, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path[:0] = ["tools", "tests/fixtures"]
import shipped_app as app  # frozen copy of the shipped app, so fixing demo-app/ never breaks these tests
from contract import run, verdict


class Correct(BaseHTTPRequestHandler):
    """Reference implementation of SCOPE.md, used only to prove the checker is not always failing."""
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        c = 1 if b.get("coupon") is None else b["coupon"]
        q = b["qty"]
        if not (isinstance(q, int) and q >= 1):
            out, code = {"error": "qty must be a whole number of 1 or more"}, 422
        elif not 0 < c <= 1:
            out, code = {"error": "coupon must be in ]0, 1]"}, 422
        else:
            out, code = {"total": b["price"] * q * c, "currency": "EUR"}, 200
        self.send_response(code); self.end_headers(); self.wfile.write(json.dumps(out).encode())
    def log_message(self, *a): pass


def serve(handler):
    s = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_port}"


app.H.log_message = lambda *a: None
demo, url = serve(app.H)
good, good_url = serve(Correct)

# Demo app as shipped: F1 holds; F2 (R01), F3 (R03), F4 (R09, security), F5 (R10, display) and F6 (R11, security) are broken.
for target in (url, "--local=tests/fixtures/shipped_app.py"):  # real HTTP and in-process must give the same facts
    assert verdict("F1", target)["verdict"] == "usage"
    failed = {c["check"]: c["observed"]["status"] for r in ("F2", "F3", "F4", "F5", "F6") for c in verdict(r, target)["failed"]}
    assert failed == {"missing coupon means no discount": 500, "null coupon means no discount": 500,
                      "coupon 10 is rejected": 200, "coupon 1.5 is rejected": 200,
                      "coupon 0 is rejected": 200, "negative coupon is rejected": 200,
                      "total comes with its currency": 200, "quantity 0 is rejected": 500,
                      "negative quantity is rejected": 500}, failed
    assert [verdict(r, target)["security"] for r in ("F2", "F3", "F4", "F5", "F6")] == [False, False, True, False, True]
assert verdict("none", url)["verdict"] == "out_of_scope"
# Project start and outages: no app yet or no server is a failed check, never a crash.
assert all(not c["pass"] for c in run("--local=tests/fixtures/not_built_yet.py"))
assert all(not c["pass"] for c in run("http://127.0.0.1:9"))

# A correct implementation passes every check, so a fix can be verified with the same tool.
assert all(c["pass"] for c in run(good_url)), [c for c in run(good_url) if not c["pass"]]
assert all(verdict(r, good_url)["verdict"] == "usage" and not verdict(r, good_url)["security"] for r in ("F2", "F3", "F4", "F5", "F6"))

# Regression gate: a hotfix may leave other bugs open, but nothing that passed may fail.
import tempfile
from contract import regress
src = open("tests/fixtures/shipped_app.py").read()
d = tempfile.mkdtemp()
fix_f6 = (src.replace("    return price * qty * coupon", "    if not (isinstance(qty, int) and qty >= 1):\n        raise ValueError('qty')\n    return price * qty * coupon")
          .replace("        except Exception as e:", "        except ValueError as e:\n            out, code = {'error': str(e)}, 422\n        except Exception as e:"))
break_f1 = src.replace("    return price * qty * coupon", "    return price * qty * coupon * 2")
for name, body in (("fix_f6.py", fix_f6), ("break_f1.py", break_f1)):
    open(f"{d}/{name}", "w").write(body)
r = regress("tests/fixtures/shipped_app.py", f"{d}/fix_f6.py")
assert r["regressions"] == [] and any(x.startswith("F6") for x in r["fixed"]) and any(x.startswith("F5") for x in r["still_open"]), r
r = regress("tests/fixtures/shipped_app.py", f"{d}/break_f1.py")
assert any(x.startswith("F1") for x in r["regressions"]), r

demo.shutdown(); good.shutdown()
print("ok")
