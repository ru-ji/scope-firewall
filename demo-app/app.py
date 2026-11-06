"""Demo shop. BUG (case B01): /pay crashes when no coupon is sent (coupon=None)."""
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
