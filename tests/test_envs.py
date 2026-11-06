"""Production never regresses: staging may only fail rules production already fails; a named approval is required."""
import os, sys, tempfile
sys.path.insert(0, "tools")
from envs import can_promote, current, load, record

p = os.path.join(tempfile.mkdtemp(), "ENVIRONMENTS.md")
assert can_promote(load(p), "asher")[0] is False                          # nothing on staging yet

record("staging", "aaa0001", 8, 11, ["F5", "F6"], "Planner", path=p)     # today's app, two open bugs
assert can_promote(load(p), "")[0] is False                               # no named approval
ok, reason, commit = can_promote(load(p), "asher")
assert ok and commit == "aaa0001" and "baseline" in reason, reason        # first promotion = production baseline
record("production", "aaa0001", 8, 11, ["F5", "F6"], "approved by asher", path=p)

record("staging", "bbb0002", 10, 11, ["F5"], "Planner", path=p)          # hotfix B11: F6 fixed, display bug F5 still open
ok, reason, commit = can_promote(load(p), "asher")
assert ok and commit == "bbb0002" and "fixes F6" in reason, reason        # the hotfix ships while F5 waits for its patch
record("production", "bbb0002", 10, 11, ["F5"], "approved by asher", path=p)

record("staging", "ccc0003", 9, 11, ["F2", "F5"], "Planner", path=p)     # a build that breaks F2, which works in prod
ok, reason, _ = can_promote(load(p), "asher")
assert not ok and "regression" in reason and "F2" in reason, reason     # refused even with the tech lead's approval
assert current("production", load(p))["Commit"] == "bbb0002"              # production untouched
print("ok")
