import csv, sys
sys.path.insert(0, "tools")
from plan_window import plan
rows = list(csv.DictReader(open("data/traffic.csv")))
assert plan(rows, "critical")["when"] == "now"
r = plan(rows, "minor")
assert r["when"] == "03:30" and r["now_requests_per_hour"] == 4000, r
print("ok")
