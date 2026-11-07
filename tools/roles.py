"""Who may do what. team.json lists each person's roles, the working days and the holidays.

The tools call require() before any decision a role owns, so an agent cannot act for the wrong person:
  project-manager  accepts or refuses a date, records a delay, signs the contract or an amendment
  developer        gives the effort of a piece of work
  tech-lead        approves a production promotion or a rollback
"""
import datetime, json, os

PATH = os.environ.get("TEAM_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "team.json")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def team(path=None):
    return json.load(open(path or PATH))


def require(name, *roles, path=None):
    have = team(path)["members"].get(name.strip().lower(), [])
    if not set(roles) & set(have):
        raise SystemExit(f"REFUSED: {name.strip() or 'nobody'} is not {' or '.join(roles)} in team.json "
                         f"(has: {', '.join(have) or 'no role'})")


def is_workday(day, path=None):
    t = team(path)
    return DAYS[day.weekday()] in t["workdays"] and day.isoformat() not in t["holidays"]


def add_workdays(start, days, path=None):
    """The working day on which `days` days of work, started on `start`, are finished."""
    day, left = start, days
    while not is_workday(day, path):
        day += datetime.timedelta(days=1)
    while left > 1:
        day += datetime.timedelta(days=1)
        if is_workday(day, path):
            left -= 1
    return day
