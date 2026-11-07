import datetime, sys
sys.path.insert(0, "tools")
import envs, scope
from roles import add_workdays, require

require("asher", "tech-lead")
require("Asher ", "project-manager")                                 # names are matched loosely
for wrong in (lambda: require("dev", "tech-lead"), lambda: require("", "project-manager"),
              lambda: envs.promote("dev"), lambda: envs.rollback("client"),     # refused before anything runs
              lambda: scope.sign("drafts/none.json", "v1.0", "dev")):
    try:
        wrong()
        raise AssertionError("should refuse")
    except SystemExit as e:
        assert "REFUSED" in str(e) and "team.json" in str(e), e
assert add_workdays(datetime.date(2026, 11, 14), 1) == datetime.date(2026, 11, 16)   # a Saturday start waits for Monday
assert add_workdays(datetime.date(2026, 11, 10), 2) == datetime.date(2026, 11, 12)   # Wednesday 11 is a holiday
print("roles ok")
