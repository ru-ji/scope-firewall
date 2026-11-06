"""Frozen copy of demo-app/app.py as shipped in v2.3.1 (with the B01/B03/B09 defects). Tests prove the contract catches these defects; demo-app/ itself can then be fixed without breaking the tests."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

def total(price, qty, coupon):
    return price * qty * coupon  # BUG: coupon None -> TypeError; should default to 1

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            out, code = {"total": total(body["price"], body["qty"], body.get("coupon"))}, 200
        except Exception as e:
            out, code = {"error": repr(e)}, 500
        self.send_response(code); self.end_headers(); self.wfile.write(json.dumps(out).encode())

if __name__ == "__main__":
    HTTPServer(("", 8080), H).serve_forever()
