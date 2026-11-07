import datetime, json, os, sys, tempfile
sys.path.insert(0, "tools")
from schedule import accept, breakdown, delay, estimate, late, lines, propose, refuse
from priorities import client_note

d = tempfile.mkdtemp()
p, t = os.path.join(d, "schedule.json"), os.path.join(d, "team.json")
json.dump({"members": {"asher": ["project-manager", "tech-lead"], "dev": ["developer"], "client": ["client"]},
           "workdays": ["Mon", "Tue", "Wed", "Thu", "Fri"], "holidays": ["2026-11-11"]}, open(t, "w"))
kw = {"path": p, "team_path": t}

# 3 small items (1 day each: build + test and confirm) and 1 medium (2 + 1): 6 working days from Monday 9,
# skipping Wednesday 11 (holiday): 9, 10, 12, 13, 16, 17
v = propose("v1.0", "2026-11-09", ["F2:S", "F4:M", "F5:S", "F6:S"], **kw)
assert v["work_days"] == 6 and v["proposed"] == "2026-11-17" and v["due"] is None, v
assert "one item at a time" in breakdown("v1.0", path=p)

v = estimate("v1.0", "F5", "M", "dev", **kw)                      # the developer knows better: +2 days
assert v["proposed"] == "2026-11-19" and v["due"] is None, v
assert "waiting for the project manager" in lines(set(), path=p)[0]

for wrong in (lambda: estimate("v1.0", "F5", "S", "asher", **kw),    # the manager does not estimate
              lambda: accept("v1.0", "dev", **kw),                   # the developer does not commit the date
              lambda: accept("v1.0", "client", **kw),
              lambda: delay("v1.0", 1, "x", "asher", **kw),          # nothing committed yet
              lambda: refuse("v1.0", "asher", " ", **kw),
              lambda: propose("v1.0", "2026-11-09", ["F2:XL"], **kw)):
    try:
        wrong()
        raise AssertionError("should refuse")
    except SystemExit:
        pass

v = accept("v1.0", "asher", **kw)
assert v["due"] == "2026-11-19" and v["accepted_by"] == "asher"
v = delay("v1.0", 2, "payment sandbox down", "asher", today=datetime.date(2026, 11, 12), **kw)
assert v["due"] == "2026-11-23", v                                  # Fri 20, then Mon 23: the weekend does not count
assert late(set(), today=datetime.date(2026, 11, 24), path=p) == ["v1.0"]
assert late({"v1.0"}, today=datetime.date(2026, 11, 24), path=p) == []
out = lines(set(), today=datetime.date(2026, 11, 24), path=p)
assert "LATE" in out[0] and "moved 2 working day(s) from 2026-11-19: payment sandbox down" in out[0], out

note = client_note({"bugs": [], "features": [], "releases": []}, out)
assert "Dates (a delay always comes with its reason):" in note and "payment sandbox down" in note
assert "Dates" not in client_note({"bugs": [], "features": [], "releases": []})
print("schedule ok")
