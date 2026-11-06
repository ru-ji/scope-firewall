"""Planner: deterministic deploy-window pick. Usage: plan_window.py traffic.csv [critical|minor] [now_hour]"""
import csv, json, sys

def plan(rows, severity="minor", now=14, width=2):
    if severity == "critical":
        return {"when": "now", "rollback": "required", "reason": "critical: do not wait for quiet window"}
    t = [int(r["requests"]) for r in rows]
    best = min(range(24), key=lambda h: sum(t[(h + i) % 24] for i in range(width)))
    return {"when": f"{best:02d}:30", "avg_requests_per_hour_in_window": sum(t[(best + i) % 24] for i in range(width)) / width,
            "now_requests_per_hour": t[now], "rollback": "required",
            "reason": f"lowest {width}h traffic starts at {best:02d}:00"}

if __name__ == "__main__":
    rows = list(csv.DictReader(open(sys.argv[1])))
    print(json.dumps(plan(rows, *(sys.argv[2:3] or ["minor"]), *(int(x) for x in sys.argv[3:4])), indent=1))
