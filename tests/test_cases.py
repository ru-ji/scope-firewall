"""Every test case is consistent with the tools: the live contract gives the expected verdict, the lane script the expected lane."""
import os
os.environ["SCOPE_FILE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "scope_demo.json")  # tests judge the frozen demo contract, whatever the live scope is
import json, sys, threading
from http.server import HTTPServer

sys.path[:0] = ["tools", "tests/fixtures"]
import shipped_app as app  # frozen copy of the shipped app, so fixing demo-app/ never breaks these tests
from contract import verdict
from triage_lane import lane

cases = json.load(open("cases/cases.json"))
assert len({c["id"] for c in cases}) == len(cases)
assert sorted(c["demo"] for c in cases if "demo" in c) == [1, 2, 3, 4, 5, 6]

app.H.log_message = lambda *a: None
s = HTTPServer(("127.0.0.1", 0), app.H)
threading.Thread(target=s.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{s.server_port}"

for c in cases:
    if c.get("expected_action"):
        assert c["expected_action"] in ("refuse", "mask") and c["expected_verdict"] is None, c["id"]
        continue
    if c["rule"] is not None:
        v = verdict(c["rule"], url)
        assert v["verdict"] == c["expected_verdict"], (c["id"], v["verdict"])
        assert v["security"] == c["security"], (c["id"], "security flag must come from the contract")
        assert verdict(c["rule"], "--local=tests/fixtures/shipped_app.py")["verdict"] == v["verdict"], (c["id"], "--local and HTTP must agree")
    got = lane(c["expected_verdict"], c["severity"], c["security"])["lane"]
    assert got == c["expected_lane"], (c["id"], got)

# One client message, two fates: the mixed message splits into free work and billed work.
mixed = [c for c in cases if c.get("mixed") == "R12"]
assert len(mixed) == 2 and len({c["report"] for c in mixed}) == 1
assert [c["expected_lane"] for c in mixed] == ["patch", "backlog"]

s.shutdown()
print("ok")
