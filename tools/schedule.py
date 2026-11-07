"""Dates of every version. The system proposes, the developer estimates, the project manager decides. Writes schedule.json.

Usage:
  schedule.py propose <version> <start YYYY-MM-DD> <item:S|M|L> [...]   date computed from the work, in working days
  schedule.py estimate <version> <item> <S|M|L> "<developer>"         a developer corrects an effort; the date is recomputed
  schedule.py accept <version> "<project manager>"                    the proposed date becomes the commitment
  schedule.py refuse <version> "<project manager>" "<reason>"
  schedule.py delay <version> <working days> "<reason>" "<project manager>"   an unexpected event moves a committed date
  schedule.py show [YYYY-MM-DD]                                        every date, its slips, and what is late

Work is done one item at a time: an item is built, then tested on staging and confirmed working before the next starts.
Days per item = build (S 0.5, M 2, L 4) + test and confirmation (S 0.5, M 1, L 1). Weekends and the holidays of
team.json are not working days. Roles come from team.json (tools/roles.py).
"""
import datetime, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roles import add_workdays, require

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schedule.json")
BUILD = {"S": 0.5, "M": 2, "L": 4}
CHECK = {"S": 0.5, "M": 1, "L": 1}


def load(path=PATH):
    return json.load(open(path)) if os.path.exists(path) else {}


def _save(s, path):
    json.dump(s, open(path, "w"), indent=2)
    open(path, "a").write("\n")


def _date(s):
    try:
        return datetime.date.fromisoformat(s)
    except (TypeError, ValueError):
        raise SystemExit(f"date must look like 2026-11-20, got {s!r}")


def _get(s, version):
    if version not in s:
        raise SystemExit(f"{version} has no proposed date yet: run `schedule.py propose` first")
    return s[version]


def _compute(v, team_path=None):
    days = sum(BUILD[i["effort"]] + CHECK[i["effort"]] for i in v["items"])
    v["work_days"] = days
    v["proposed"] = add_workdays(_date(v["start"]), math.ceil(days), team_path).isoformat()


def propose(version, start, items, path=PATH, team_path=None):
    parsed = []
    for it in items:
        name, _, effort = it.rpartition(":")
        if not name or effort not in BUILD:
            raise SystemExit(f"item must look like F5:M (effort S, M or L), got {it!r}")
        parsed.append({"id": name, "effort": effort, "by": "system"})
    if not parsed:
        raise SystemExit("give at least one item")
    s = load(path)
    v = s.setdefault(version, {"due": None, "accepted_by": None, "slips": []})
    v.update(start=_date(start).isoformat(), items=parsed, status="proposed")
    _compute(v, team_path)
    _save(s, path)
    return v


def estimate(version, item, effort, developer, path=PATH, team_path=None):
    require(developer, "developer", path=team_path)
    if effort not in BUILD:
        raise SystemExit("effort must be S, M or L")
    s = load(path)
    v = _get(s, version)
    hit = [i for i in v["items"] if i["id"] == item]
    if not hit:
        raise SystemExit(f"{item} is not planned in {version}")
    hit[0].update(effort=effort, by=developer.strip())
    v["status"] = "proposed"
    _compute(v, team_path)
    _save(s, path)
    return v


def accept(version, manager, path=PATH, team_path=None):
    require(manager, "project-manager", path=team_path)
    s = load(path)
    v = _get(s, version)
    v.update(due=v["proposed"], accepted_by=manager.strip(), status="accepted")
    _save(s, path)
    return v


def refuse(version, manager, reason, path=PATH, team_path=None):
    require(manager, "project-manager", path=team_path)
    if not reason.strip():
        raise SystemExit("a refusal needs a reason")
    s = load(path)
    v = _get(s, version)
    v.update(status="refused", refused=f"{manager.strip()}: {' '.join(reason.split())}")
    _save(s, path)
    return v


def delay(version, days, reason, manager, today=None, path=PATH, team_path=None):
    require(manager, "project-manager", path=team_path)
    s = load(path)
    v = _get(s, version)
    if not v.get("due"):
        raise SystemExit(f"{version} has no committed date: the project manager accepts one first")
    if not str(days).isdigit() or int(days) < 1 or not reason.strip():
        raise SystemExit("days must be a whole number of working days, 1 or more, and the reason cannot be empty")
    new = add_workdays(_date(v["due"]) + datetime.timedelta(days=1), int(days), team_path)
    v["slips"].append({"from": v["due"], "to": new.isoformat(), "working_days": int(days),
                       "reason": " ".join(reason.split()), "by": manager.strip(),
                       "reported": (today or datetime.date.today()).isoformat()})
    v["due"] = v["proposed"] = new.isoformat()
    _save(s, path)
    return v


def breakdown(version, path=PATH):
    v = _get(load(path), version)
    parts = [f"{i['id']} {i['effort']} ({BUILD[i['effort']]} build + {CHECK[i['effort']]} test and confirm, by {i['by']})"
             for i in v["items"]]
    return (f"{version}: {v['work_days']} working days from {v['start']}, one item at a time -> proposed {v['proposed']}"
            f" [{v['status']}]\n  " + "\n  ".join(parts))


def late(delivered, today=None, path=PATH):
    today = today or datetime.date.today()
    return sorted(k for k, v in load(path).items() if v.get("due") and k not in delivered and _date(v["due"]) < today)


def lines(delivered, today=None, path=PATH):
    today = today or datetime.date.today()
    out = []
    for k, v in sorted(load(path).items(), key=lambda kv: kv[1].get("due") or kv[1]["proposed"]):
        if not v.get("due"):
            out.append(f"- {k} proposed {v['proposed']}, waiting for the project manager ({v['status']})")
            continue
        state = "delivered" if k in delivered else ("LATE" if _date(v["due"]) < today else "on time")
        slips = "; ".join(f"moved {x['working_days']} working day(s) from {x['from']}: {x['reason']}" for x in v["slips"])
        out.append(f"- {k} due {v['due']} ({state}, accepted by {v['accepted_by']})" + (f", {slips}" if slips else ""))
    return out


def delivered_now():
    import priorities, versions
    return versions.delivered_versions(priorities.VERSIONS) | {r["Release"] for r in priorities.load() if r["Status"] == "done"}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["propose"] and len(a) >= 4:
        propose(a[1], a[2], a[3:])
        print(breakdown(a[1]))
    elif a[:1] == ["estimate"] and len(a) == 5:
        estimate(*a[1:])
        print(breakdown(a[1]))
    elif a[:1] == ["accept"] and len(a) == 3:
        v = accept(*a[1:])
        print(f"{a[1]} committed for {v['due']}, accepted by {v['accepted_by']}")
    elif a[:1] == ["refuse"] and len(a) == 4:
        refuse(*a[1:])
        print(f"{a[1]} date refused: {a[3]}")
    elif a[:1] == ["delay"] and len(a) == 5:
        v = delay(*a[1:])
        print(f"{a[1]} now due {v['due']}: {v['slips'][-1]['reason']}")
    elif a[:1] == ["show"] and len(a) in (1, 2):
        today = _date(a[1]) if len(a) == 2 else None
        print("\n".join(lines(delivered_now(), today) or ["(no date yet)"]))
        print("LATE: " + (", ".join(late(delivered_now(), today)) or "none"))
    else:
        print(__doc__)
        sys.exit(2)
