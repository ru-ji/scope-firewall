import datetime, os, sys, tempfile
sys.path.insert(0, "tools")
from schedule import delay, due, late, lines
from priorities import client_note

p = os.path.join(tempfile.mkdtemp(), "schedule.json")
d = datetime.date
due("v1.0.1", "2026-11-07", "Planner", path=p)
due("v1.1", "2026-11-20", "Planner", path=p)
v = delay("v1.1", 1, "hotfix R14a goes first", "Planner", today=d(2026, 11, 7), path=p)
assert v["due"] == "2026-11-21" and v["slips"][0]["from"] == "2026-11-20", v
assert late(set(), today=d(2026, 11, 8), path=p) == ["v1.0.1"]
assert late({"v1.0.1"}, today=d(2026, 11, 8), path=p) == []
out = lines(set(), today=d(2026, 11, 8), path=p)
assert "LATE" in out[0] and "moved 1 day(s) from 2026-11-20: hotfix R14a goes first" in out[1], out

for bad in (lambda: delay("v9.9", 1, "x", "P", path=p), lambda: delay("v1.1", 0, "x", "P", path=p),
            lambda: delay("v1.1", 2, " ", "P", path=p), lambda: due("v1.2", "next week", "P", path=p)):
    try:
        bad()
        raise AssertionError("should refuse")
    except SystemExit:
        pass

note = client_note({"bugs": [], "features": [], "releases": []}, out)
assert "Dates (a delay always comes with its reason):" in note and "hotfix R14a goes first" in note
assert "Dates" not in client_note({"bugs": [], "features": [], "releases": []})
print("schedule ok")
