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
# Deliverables: the security fix ships alone now; the rest ship together in the quiet window; features in v1.1.
assert [(r["version"], r["kind"], r["items"]) for r in p["releases"]] == [
    ("v1.0.1", "hotfix", ["B11"]), ("v1.0.2", "patch", ["B12", "B03", "B10"]), ("v1.1", "features", ["CR-001", "CR-002"])]
assert "1. B11 [high, security]" in render(p) and "v1.0.1 hotfix, now: B11" in render(p)

assert done("B11", path=q, versions=v) == "v1.0.1"
assert [r["Id"] for r in ranked(load(q))] == ["B12", "B03", "B10"]
# After v1.0.1 shipped, the next deliverable is v1.0.2: version numbers never go back.
assert [(r["version"], r["items"]) for r in make_plan(load(q), 14, versions=v)["releases"]][0] == ("v1.0.2", ["B12", "B03", "B10"])
add("B12", "defect", "critical", "no", "wrong tax on every order", "40", path=q)  # re-assessed: updated, not duplicated
assert [r["Id"] for r in ranked(load(q))] == ["B12", "B03", "B10"] and len(load(q)) == 4

for bad in (lambda: add("X1", "defect", "low", "no", "t", path=q), lambda: add("B20", "out_of_scope", "low", "no", "t", path=q),
            lambda: add("B20", "defect", "urgent", "no", "t", path=q), lambda: done("B99", path=q, versions=v), lambda: done("B11", path=q, versions=v)):
    try:
        bad(); raise AssertionError("should have refused")
    except SystemExit:
        pass
print("ok")
