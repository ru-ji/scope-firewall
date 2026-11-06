import sys
sys.path.insert(0, "tools")
from triage_lane import lane
assert lane("defect", "critical")["lane"] == "hotfix"
assert lane("defect", "low", security=True)["lane"] == "hotfix"
assert lane("defect", "medium")["lane"] == "patch"
assert lane("defect", "high")["lane"] == "patch"
assert lane("usage")["lane"] == "reply"
assert lane("out_of_scope", "high")["lane"] == "backlog"
assert lane("external")["lane"] == "watch"
assert lane("uncertain")["lane"] == "human"
for bad in (("bug", "low"), ("defect", "urgent")):
    try:
        lane(*bad); raise AssertionError(bad)
    except ValueError:
        pass
print("ok")
