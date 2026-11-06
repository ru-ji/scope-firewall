"""Planner: deterministic exit lane. Usage: triage_lane.py <verdict> [severity] [security]
verdict: defect|usage|out_of_scope|external|uncertain ; severity: critical|high|medium|low"""
import json, sys

VERDICTS = ("defect", "usage", "out_of_scope", "external", "uncertain")
SEVERITIES = ("critical", "high", "medium", "low")


def lane(verdict, severity="low", security=False):
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}")
    if verdict == "usage":
        return {"lane": "reply", "why": "behaviour matches SCOPE.md: draft a reply to the client, no code change"}
    if verdict == "out_of_scope":
        return {"lane": "backlog", "why": "not in SCOPE.md: VERSIONS.md row + quote, never in the MVP"}
    if verdict == "external":
        return {"lane": "watch", "why": "third-party cause: monitor, no fix"}
    if verdict == "uncertain":
        return {"lane": "human", "why": "not enough evidence: a human decides"}
    if security or severity == "critical":
        return {"lane": "hotfix", "why": "security hole or critical outage: PR + tech lead approval + rollback plan, now"}
    return {"lane": "patch", "why": "non-blocking defect: next patch release, deployed in the quiet window (plan_window.py)"}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(2)
    print(json.dumps(lane(a[0], *(a[1:2] or ["low"]), security="security" in a[2:]), indent=1))
