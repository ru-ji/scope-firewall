import os, sys, tempfile
sys.path.insert(0, "tools")
from versions import add, status

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

assert open("SCOPE.md").read() == scope_before  # the frozen MVP is never touched
print("ok")
