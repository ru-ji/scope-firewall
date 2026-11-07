"""Planner: target dates of every version, delays and their reasons. Writes schedule.json.

Usage:
  schedule.py due <version> <YYYY-MM-DD> "<set by>"            target date (kickoff, accepted quote, planned hotfix)
  schedule.py delay <version> <days> "<reason>" "<reported by>"  an unexpected event: moves the date, keeps the reason
  schedule.py show [YYYY-MM-DD]                                   every date, its slips, and what is late today

A version is late when its date has passed and it is not delivered (VERSIONS.md, or a QUEUE.md release marked done).
"""
import datetime, json, os, sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schedule.json")


def load(path=PATH):
    return json.load(open(path)) if os.path.exists(path) else {}


def _save(s, path):
    json.dump(s, open(path, "w"), indent=2)
    open(path, "a").write("\n")


def _date(s):
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        raise SystemExit(f"date must look like 2026-11-20, got {s!r}")


def due(version, date, by, path=PATH):
    s = load(path)
    s.setdefault(version, {"slips": []}).update(due=_date(date).isoformat(), set_by=by.strip())
    _save(s, path)
    return s[version]


def delay(version, days, reason, by, today=None, path=PATH):
    s = load(path)
    if version not in s:
        raise SystemExit(f"{version} has no date yet: set one with `schedule.py due` first")
    if not str(days).isdigit() or int(days) < 1 or not reason.strip():
        raise SystemExit("days must be a whole number of 1 or more, and the reason cannot be empty")
    v = s[version]
    new = _date(v["due"]) + datetime.timedelta(days=int(days))
    v["slips"].append({"from": v["due"], "to": new.isoformat(), "days": int(days), "reason": " ".join(reason.split()),
                       "by": by.strip(), "reported": (today or datetime.date.today()).isoformat()})
    v["due"] = new.isoformat()
    _save(s, path)
    return v


def late(delivered, today=None, path=PATH):
    today = today or datetime.date.today()
    return sorted(v for v, d in load(path).items() if v not in delivered and _date(d["due"]) < today)


def lines(delivered, today=None, path=PATH):
    today = today or datetime.date.today()
    out = []
    for v, d in sorted(load(path).items(), key=lambda kv: kv[1]["due"]):
        state = "delivered" if v in delivered else ("LATE" if _date(d["due"]) < today else "on time")
        slips = "; ".join(f"moved {x['days']} day(s) from {x['from']}: {x['reason']}" for x in d["slips"])
        out.append(f"- {v} due {d['due']} ({state})" + (f", {slips}" if slips else ""))
    return out


def delivered_now():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import priorities, versions
    return versions.delivered_versions(priorities.VERSIONS) | {r["Release"] for r in priorities.load() if r["Status"] == "done"}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["due"] and len(a) == 4:
        print(a[1], due(*a[1:]))
    elif a[:1] == ["delay"] and len(a) == 5:
        print(a[1], delay(*a[1:]))
    elif a[:1] == ["show"] and len(a) in (1, 2):
        today = _date(a[1]) if len(a) == 2 else None
        print("\n".join(lines(delivered_now(), today) or ["(no date set)"]))
        print("LATE: " + (", ".join(late(delivered_now(), today)) or "none"))
    else:
        print(__doc__)
        sys.exit(2)
