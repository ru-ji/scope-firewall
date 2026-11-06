import os, sys, tempfile
sys.path.insert(0, "tools")
import contract
from versions import add, delivered_versions, next_version, status

tmp = os.path.join(tempfile.mkdtemp(), "VERSIONS.md")
open(tmp, "w").writelines(l for l in open("VERSIONS.md") if "| CR-" not in l)  # independent of CRs already logged
scope_before = open("SCOPE.md").read()

cid, quote = add("PDF export of orders", "M", "WhatsApp, 2026-11-05", "new route + PDF lib", path=tmp)
assert cid == "CR-001" and "v1.1" in quote and "billed separately" in quote
assert add("CSV | export", "S", "Slack", "demo-app/app.py", path=tmp)[0] == "CR-002"
status("CR-001", "quote-sent", path=tmp)
rows = [l for l in open(tmp) if "| CR-" in l]
assert rows[0].rstrip().endswith("| quote-sent |") and rows[1].rstrip().endswith("| proposed |"), rows
assert "CSV / export" in rows[1]  # pipe cannot break the table

for bad in (lambda: add("x", "XL", "o", "f", path=tmp), lambda: add("x", "S", "o", "f", "v1.0", path=tmp),
            lambda: status("CR-999", "accepted", path=tmp), lambda: status("CR-001", "done", path=tmp)):
    try:
        bad(); raise AssertionError("should have refused")
    except SystemExit:
        pass

# A change request is delivered only when the rules signed for it pass.
real_run, real_scope = contract.run, contract.SCOPE
contract.SCOPE = {"amendments": [{"cr": "CR-001", "rules": ["F7"]}]}
contract.run = lambda *a: [{"rule": "F7", "pass": False}]
try:
    status("CR-001", "delivered", path=tmp); raise AssertionError("F7 still fails")
except SystemExit as e:
    assert "F7" in str(e)
contract.run = lambda *a: [{"rule": "F7", "pass": True}]
status("CR-002", "accepted", path=tmp)
status("CR-001", "delivered", path=tmp)
contract.run, contract.SCOPE = real_run, real_scope
assert "v1.1" not in delivered_versions(tmp) and next_version(tmp) == "v1.1"   # CR-002, accepted, is still in v1.1
status("CR-002", "delivered", path=tmp)
assert "v1.1" in delivered_versions(tmp) and next_version(tmp) == "v1.2"
cid, quote = add("Next thing", "S", "Slack", "x", path=tmp)
assert cid == "CR-003" and "v1.2" in quote                                     # never quoted into a shipped version

assert open("SCOPE.md").read() == scope_before  # the frozen MVP is never touched
print("ok")
