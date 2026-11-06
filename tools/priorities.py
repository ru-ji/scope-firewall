"""Planner: ranks every open bug and plans bugs AND features. Writes QUEUE.md.

Usage:
  priorities.py add <id> <verdict> <severity> <security yes|no> "<title>" [affected clients]
  priorities.py done <id>
  priorities.py plan [current hour]          ranked plan: bugs by priority, then features by version

Rank: security holes first, then severity (critical > high > medium > low), then clients affected, then oldest.
Plan: hotfix lane -> now, in rank order; patch lane -> next quiet window (plan_window.py), in rank order;
features -> VERSIONS.md change requests, accepted first, then quote-sent, then proposed; smaller effort first.
"""
import csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan_window import plan as window
from triage_lane import SEVERITIES, lane

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
QUEUE, VERSIONS, TRAFFIC = (os.path.join(ROOT, f) for f in ("QUEUE.md", "VERSIONS.md", "data/traffic.csv"))
COLS = ["Id", "Title", "Verdict", "Severity", "Security", "Affected", "Order", "Status"]
HEADER = ("# QUEUE: open bugs, ranked\n\nWritten by `tools/priorities.py`. Rank: security first, then severity, then clients "
          "affected, then oldest.\n\n| " + " | ".join(COLS) + " |\n|" + " --- |" * len(COLS) + "\n")


def _cell(s):
    return " ".join(str(s).split()).replace("|", "/")


def load(path=QUEUE):
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| B") and len(cells) == len(COLS):
            rows.append(dict(zip(COLS, cells)))
    return rows


def save(rows, path=QUEUE):
    with open(path, "w") as f:
        f.write(HEADER + "".join("| " + " | ".join(_cell(r[c]) for c in COLS) + " |\n" for r in rows))


def add(bid, verdict, severity, security, title, affected="0", path=QUEUE):
    if not re.fullmatch(r"B\d+", bid):
        raise SystemExit("id must look like B12")
    if verdict != "defect":
        raise SystemExit("only confirmed defects go in the bug queue; out_of_scope goes to VERSIONS.md")
    if severity not in SEVERITIES or security not in ("yes", "no") or not str(affected).isdigit():
        raise SystemExit(f"severity in {SEVERITIES}, security yes|no, affected a whole number")
    rows = [r for r in load(path) if r["Id"] != bid]
    order = max([int(r["Order"]) for r in load(path)] or [0]) + 1
    rows.append({"Id": bid, "Title": title, "Verdict": verdict, "Severity": severity, "Security": security,
                 "Affected": str(affected), "Order": str(order), "Status": "open"})
    save(rows, path)


def done(bid, path=QUEUE):
    rows = load(path)
    if bid not in [r["Id"] for r in rows]:
        raise SystemExit(f"{bid} not in the queue")
    for r in rows:
        if r["Id"] == bid:
            r["Status"] = "done"
    save(rows, path)


def ranked(rows):
    open_rows = [r for r in rows if r["Status"] == "open"]
    return sorted(open_rows, key=lambda r: (r["Security"] != "yes", SEVERITIES.index(r["Severity"]),
                                            -int(r["Affected"]), int(r["Order"])))


def features(path=VERSIONS):
    if not os.path.exists(path):
        return []
    status_rank = {"accepted": 0, "quote-sent": 1, "proposed": 2}
    out = []
    for line in open(path):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[1].startswith("CR-") and cells[6] in status_rank:
            out.append({"version": cells[0], "id": cells[1], "request": cells[3], "effort": cells[4], "status": cells[6]})
    return sorted(out, key=lambda f: (f["version"], status_rank[f["status"]], "SML".index(f["effort"]), f["id"]))


def make_plan(rows, now=14, versions=VERSIONS, traffic=TRAFFIC):
    quiet = window(list(csv.DictReader(open(traffic))), "minor", now)["when"]
    bugs = []
    for rank, r in enumerate(ranked(rows), 1):
        l = lane("defect", r["Severity"], r["Security"] == "yes")["lane"]
        bugs.append({"rank": rank, **r, "lane": l, "slot": "now" if l == "hotfix" else f"quiet window {quiet}"})
    return {"bugs": bugs, "features": features(versions)}


def render(p):
    out = ["BUGS, by priority"]
    for b in p["bugs"]:
        sec = ", security" if b["Security"] == "yes" else ""
        out.append(f"{b['rank']}. {b['Id']} [{b['Severity']}{sec}] {b['Title']} -> {b['lane']} {b['slot']}")
    if not p["bugs"]:
        out.append("(no open bug)")
    out.append("FEATURES, by version")
    for f in p["features"]:
        out.append(f"{f['version']} {f['id']} [{f['status']}, effort {f['effort']}] {f['request']}")
    if not p["features"]:
        out.append("(no change request)")
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["add"] and len(a) in (6, 7):
        add(*a[1:])
        print(render(make_plan(load())))
    elif a[:1] == ["done"] and len(a) == 2:
        done(a[1])
        print(render(make_plan(load())))
    elif a[:1] == ["plan"] and len(a) in (1, 2):
        print(render(make_plan(load(), *(int(x) for x in a[1:2]))))
    else:
        print(__doc__)
        sys.exit(2)
