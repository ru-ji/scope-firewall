"""The contract checker must flag the shipped app's real defects (frozen in tests/fixtures) AND pass a correct implementation."""
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
        out, code = ({"total": b["price"] * b["qty"] * c}, 200) if 0 < c <= 1 else ({"error": "coupon must be in ]0, 1]"}, 422)
        self.send_response(code); self.end_headers(); self.wfile.write(json.dumps(out).encode())
    def log_message(self, *a): pass


def serve(handler):
    s = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_port}"


app.H.log_message = lambda *a: None
demo, url = serve(app.H)
good, good_url = serve(Correct)

# Demo app as shipped: F1 holds; F2 (B01), F3 (B03) and F4 (B09, security) are broken.
for target in (url, "--local=tests/fixtures/shipped_app.py"):  # real HTTP and in-process must give the same facts
    assert verdict("F1", target)["verdict"] == "usage"
    failed = {c["check"]: c["observed"]["status"] for r in ("F2", "F3", "F4") for c in verdict(r, target)["failed"]}
    assert failed == {"missing coupon means no discount": 500, "null coupon means no discount": 500,
                      "coupon 10 is rejected": 200, "coupon 1.5 is rejected": 200,
                      "coupon 0 is rejected": 200, "negative coupon is rejected": 200}, failed
    assert [verdict(r, target)["security"] for r in ("F2", "F3", "F4")] == [False, False, True]
assert verdict("none", url)["verdict"] == "out_of_scope"

# A correct implementation passes every check, so a fix can be verified with the same tool.
assert all(c["pass"] for c in run(good_url)), [c for c in run(good_url) if not c["pass"]]
assert all(verdict(r, good_url)["verdict"] == "usage" and not verdict(r, good_url)["security"] for r in ("F2", "F3", "F4"))

demo.shutdown(); good.shutdown()
print("ok")
