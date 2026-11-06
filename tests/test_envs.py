"""Production never regresses: staging may only fail rules production already fails; a named approval is required."""
import os, sys, tempfile
os.environ["SCOPE_FILE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "scope_demo.json")  # the frozen demo contract, whatever the live scope is
sys.path.insert(0, "tools")
import envs
from contract import SCOPE
from envs import can_promote, current, failing_at, load, record, rollback_target

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

# An amendment adds F7, not built yet: both commits fail it, so it is no regression and a patch still ships.
record("staging", "ddd0004", 10, 12, ["F7"], "Planner", path=p)          # fixes F5; F7 was unknown when prod was recorded
assert not can_promote(load(p), "asher")[0]                               # the ledger alone would say "F7 works in production"
today = {"bbb0002": {"F5", "F7"}, "ddd0004": {"F7"}}                      # judged with today's contract
ok, reason, commit = can_promote(load(p), "asher", lambda r: today[r["Commit"]])
assert ok and commit == "ddd0004" and "fixes F5" in reason, reason
envs.SCOPE = {**SCOPE, "app": "tests/fixtures/shipped_app.py"}             # a file every commit has, with known failures
assert failing_at({"Commit": "HEAD"}) == {"F2", "F3", "F4", "F5", "F6"}     # a real commit is really judged
assert failing_at({"Commit": "0" * 40}) == {r["id"] for r in SCOPE["rules"]}  # no such commit: nothing can be claimed to work

# Rollback steps back one release at a time, with a named approval.
assert rollback_target(load(p), "")[0] is False
record("production", "ddd0004", 11, 12, ["F7"], "approved by asher", path=p)
ok, reason, commit = rollback_target(load(p), "asher")
assert ok and commit == "bbb0002", reason
record("production", "bbb0002", 10, 12, ["F5", "F7"], "rollback approved by asher", path=p)
assert rollback_target(load(p), "asher")[2] == "aaa0001"                  # never flips back to the bad release
record("production", "aaa0001", 8, 12, ["F5", "F6", "F7"], "rollback approved by asher", path=p)
assert rollback_target(load(p), "asher")[0] is False                      # nothing older
print("ok")
