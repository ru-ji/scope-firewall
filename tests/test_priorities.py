"""A payment bug always beats a display bug; security beats severity; features are planned by version."""
import os, sys, tempfile
sys.path.insert(0, "tools")
from priorities import add, done, load, make_plan, ranked, render

d = tempfile.mkdtemp()
q, v = os.path.join(d, "QUEUE.md"), os.path.join(d, "VERSIONS.md")
open(v, "w").write("| Version | Id | Origin | Request | Effort | Files | Status |\n| --- | --- | --- | --- | --- | --- | --- |\n"
                   "| v1.1 | CR-002 | Slack | Dashboard | L | x | proposed |\n"
                   "| v1.1 | CR-001 | Slack | PDF export | M | x | accepted |\n"
                   "| v1.1 | CR-003 | Mail | CSV export | S | x | rejected |\n")

# Reported in this order: display first, then a wrong-amount bug, then a payment security hole.
add("B10", "defect", "low", "no", "currency missing on the checkout page", "120", path=q)
add("B03", "defect", "high", "no", "coupon=10 charged 10 times", "3", path=q)
add("B11", "defect", "high", "yes", "negative quantity gives a negative total", "1", path=q)
add("B12", "defect", "high", "no", "wrong tax on some orders", "40", path=q)

assert [r["Id"] for r in ranked(load(q))] == ["B11", "B12", "B03", "B10"]  # security, then affected, display last
p = make_plan(load(q), 14, versions=v)
assert [(b["Id"], b["lane"], b["slot"]) for b in p["bugs"]] == [
    ("B11", "hotfix", "now"), ("B12", "patch", "quiet window 03:30"),
    ("B03", "patch", "quiet window 03:30"), ("B10", "patch", "quiet window 03:30")]
assert [f["id"] for f in p["features"]] == ["CR-001", "CR-002"]  # accepted before proposed, rejected dropped
assert "1. B11 [high, security]" in render(p)

done("B11", path=q)
assert [r["Id"] for r in ranked(load(q))] == ["B12", "B03", "B10"]
add("B12", "defect", "critical", "no", "wrong tax on every order", "40", path=q)  # re-assessed: updated, not duplicated
assert [r["Id"] for r in ranked(load(q))] == ["B12", "B03", "B10"] and len(load(q)) == 4

for bad in (lambda: add("X1", "defect", "low", "no", "t", path=q), lambda: add("B20", "out_of_scope", "low", "no", "t", path=q),
            lambda: add("B20", "defect", "urgent", "no", "t", path=q), lambda: done("B99", path=q)):
    try:
        bad(); raise AssertionError("should have refused")
    except SystemExit:
        pass
print("ok")
