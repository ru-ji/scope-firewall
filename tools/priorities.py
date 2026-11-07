"""Planner: ranks every open bug and plans bugs AND features. Writes QUEUE.md.

Usage:
  priorities.py add <id> <verdict> <severity> <security yes|no> "<title>" [affected clients]
  priorities.py done <id>
  priorities.py plan [current hour]     ranked bugs, then the deliverables: releases with their contents
  priorities.py client [current hour]   draft update for the client: included in the contract, billed, waiting for them,
                                        and every target date with its delays (schedule.py)

Rank: security holes first, then severity (critical > high > medium > low), then clients affected, then oldest.
Deliverables: every hotfix-lane bug ships in the next patch version, now; every patch-lane bug ships in the
version after it, in the next quiet window (plan_window.py); features ship in the version VERSIONS.md gives them
(accepted first, then quote-sent, then proposed; smaller effort first). Versions count up from the last delivered
version in VERSIONS.md and from the releases already shipped (bugs marked done).
"""
import csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan_window import plan as window
from triage_lane import SEVERITIES, lane
from versions import delivered_versions

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
QUEUE, VERSIONS, TRAFFIC = (os.path.join(ROOT, f) for f in ("QUEUE.md", "VERSIONS.md", "data/traffic.csv"))
COLS = ["Id", "Title", "Verdict", "Severity", "Security", "Affected", "Order", "Status", "Release"]
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
        if line.startswith("| R") and len(cells) == len(COLS):
            rows.append(dict(zip(COLS, cells)))
    return rows


def save(rows, path=QUEUE):
    with open(path, "w") as f:
        f.write(HEADER + "".join("| " + " | ".join(_cell(r[c]) for c in COLS) + " |\n" for r in rows))


def add(bid, verdict, severity, security, title, affected="0", path=QUEUE):
    if not re.fullmatch(r"R\d+[a-z]?", bid):
        raise SystemExit("id must look like R12 or R12a")
    if verdict != "defect":
        raise SystemExit("only confirmed defects go in the bug queue; out_of_scope goes to VERSIONS.md")
    if severity not in SEVERITIES or security not in ("yes", "no") or not str(affected).isdigit():
        raise SystemExit(f"severity in {SEVERITIES}, security yes|no, affected a whole number")
    rows = [r for r in load(path) if r["Id"] != bid]
    order = max([int(r["Order"]) for r in load(path)] or [0]) + 1
    rows.append({"Id": bid, "Title": title, "Verdict": verdict, "Severity": severity, "Security": security,
                 "Affected": str(affected), "Order": str(order), "Status": "open", "Release": "-"})
    save(rows, path)


def done(bid, path=QUEUE, versions=VERSIONS, traffic=TRAFFIC):
    rows = load(path)
    if bid not in [r["Id"] for r in rows if r["Status"] == "open"]:
        raise SystemExit(f"{bid} is not an open bug in the queue")
    shipped_in = next(rel["version"] for rel in make_plan(rows, versions=versions, traffic=traffic)["releases"]
                      if bid in rel["items"])
    for r in rows:
        if r["Id"] == bid:
            r["Status"], r["Release"] = "done", shipped_in
    save(rows, path)
    return shipped_in


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


def base_version(rows, versions=VERSIONS):
    """Last delivered minor (e.g. v1.0) and the highest patch number already shipped on it."""
    minor = max(delivered_versions(versions) or ["v1.0"], key=lambda v: tuple(int(x) for x in v[1:].split(".")))
    shipped = [int(r["Release"].rsplit(".", 1)[1]) for r in rows
               if r["Status"] == "done" and r["Release"].startswith(minor + ".")]
    return minor, max(shipped or [0])


def pending_build(rules, failing, delivered):
    """The developer's queue: rules of versions not delivered yet that the app does not pass."""
    out = {}
    for r in rules:
        v = r.get("version", "v1.0")
        if v not in delivered and r["id"] in failing:
            out.setdefault(v, []).append(f"{r['id']} {r['feature']}")
    return out


def build_items(versions=VERSIONS):
    import contract
    failing = {c["rule"] for c in contract.run("--local") if not c["pass"]}
    return pending_build(contract.SCOPE["rules"], failing, delivered_versions(versions))  # app missing: every rule is listed


def make_plan(rows, now=14, versions=VERSIONS, traffic=TRAFFIC, build="auto", signed=None):
    quiet = window(list(csv.DictReader(open(traffic))), "minor", now)["when"]
    bugs = []
    for rank, r in enumerate(ranked(rows), 1):
        l = lane("defect", r["Severity"], r["Security"] == "yes")["lane"]
        bugs.append({"rank": rank, **r, "lane": l, "slot": "now" if l == "hotfix" else f"quiet window {quiet}"})
    minor, patch = base_version(rows, versions)
    releases = []
    for l, when in (("hotfix", "now"), ("patch", f"quiet window {quiet}")):
        items = [b["Id"] for b in bugs if b["lane"] == l]
        if items:
            patch += 1
            releases.append({"version": f"{minor}.{patch}", "kind": l, "when": when, "items": items})
    if build == "auto":
        import contract
        build, signed = build_items(versions), contract.SCOPE.get("frozen", False)
    if signed is False:
        releases.append({"version": "v1.0", "kind": "kickoff", "when": "waiting for a client brief and a signature",
                         "items": ["the contract is not signed yet"]})
    for v, items in (build or {}).items():
        releases.append({"version": v, "kind": "build", "when": "developer's queue, built by pull request", "items": items})
    feats = features(versions)
    for v in dict.fromkeys(f["version"] for f in feats):
        releases.append({"version": v, "kind": "features", "when": "after written client approval",
                         "items": [f["id"] for f in feats if f["version"] == v]})
    return {"bugs": bugs, "features": feats, "releases": releases}


def render(p):
    out = ["BUGS, by priority"]
    for b in p["bugs"]:
        sec = ", security" if b["Security"] == "yes" else ""
        out.append(f"{b['rank']}. {b['Id']} [{b['Severity']}{sec}] {b['Title']} -> {b['lane']} {b['slot']}")
    if not p["bugs"]:
        out.append("(no open bug)")
    out.append("DELIVERABLES")
    feats = {f["id"]: f for f in p["features"]}
    for rel in p["releases"]:
        names = ", ".join(i if i not in feats else f"{i} {feats[i]['request']} [{feats[i]['status']}, effort {feats[i]['effort']}]"
                          for i in rel["items"])
        out.append(f"{rel['version']} {rel['kind']}, {rel['when']}: {names}")
    if not p["releases"]:
        out.append("(nothing planned)")
    return "\n".join(out)


def client_note(p, dates=()):
    """What the client needs to know, in their words: a draft a human reads and sends."""
    titles = {b["Id"]: b["Title"] for b in p["bugs"]}
    free = [f"- {r['version']}, {r['when']}: {', '.join(titles[i] for i in r['items'])}" for r in p["releases"]
            if r["kind"] in ("hotfix", "patch")]
    free += [f"- {r['version']}, in progress: {', '.join(r['items'])}" for r in p["releases"] if r["kind"] == "build"]
    billed = [f"- {f['version']}: {f['request']} (accepted)" for f in p["features"] if f["status"] == "accepted"]
    waiting = [f"- {f['version']}: {f['request']} (quote {f['id']})" for f in p["features"] if f["status"] != "accepted"]
    return "\n".join(["DRAFT client update (a human sends it)", "Included in your contract, no extra cost:", *(free or ["- nothing open"]),
                      "Outside the contract, billed separately:", *(billed or ["- nothing accepted"]),
                      "Waiting for your written approval:", *(waiting or ["- nothing"]),
                      *(["Dates (a delay always comes with its reason):", *dates] if dates else [])])


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["add"] and len(a) in (6, 7):
        add(*a[1:])
        print(render(make_plan(load())))
    elif a[:1] == ["done"] and len(a) == 2:
        print(f"{a[1]} shipped in {done(a[1])}")
        print(render(make_plan(load())))
    elif a[:1] == ["client"] and len(a) in (1, 2):
        import schedule
        print(client_note(make_plan(load(), *(int(x) for x in a[1:2])), schedule.lines(schedule.delivered_now())))
    elif a[:1] == ["plan"] and len(a) in (1, 2):
        print(render(make_plan(load(), *(int(x) for x in a[1:2]))))
    else:
        print(__doc__)
        sys.exit(2)
