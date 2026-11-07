"""The contract is signed once, then only changes through an amendment for a change request the client accepted."""
import datetime, json, os, shutil, sys, tempfile

d = tempfile.mkdtemp()
os.environ["SCOPE_FILE"] = os.path.join(d, "scope.json")
sys.path.insert(0, "tools")
import scope as sc

json.dump({"version": "v1.0", "endpoint": "/pay", "app": "demo-app/app.py", "frozen": False, "rules": []}, open(os.environ["SCOPE_FILE"], "w"))
open(os.path.join(d, "VERSIONS.md"), "w").write(
    "| Version | Id | Origin | Request | Effort | Files | Status |\n| --- | --- | --- | --- | --- | --- | --- |\n"
    "| v1.0 | MVP | kickoff | rules | n/a | app | planned |\n"
    "| v1.1 | CR-001 | Slack | order reference | S | app | proposed |\n")

rule = lambda i, name, sec=False: {"id": i, "feature": f"Feature {i}", "security": sec, "text": f"Rule {i} text",
                                   "checks": [{"name": name, "body": {"price": 10, "qty": 2}, "status": 200, "total": 20}]}
bad = [{"id": "F9", "feature": "a|b", "security": "no", "text": "", "checks": []}]
errs = sc.validate(bad)
assert len(errs) >= 4, errs                                              # id, pipe, security, empty text/checks
assert sc.validate([rule("F1", "a"), rule("F1", "b")])                   # duplicate id refused
assert sc.validate([rule("F1", "a"), rule("F2", "a")])                   # duplicate check name refused
assert sc.validate([{**rule("F1", "a"), "checks": [{"name": "n", "body": "x", "status": "200"}]}])
assert sc.validate([rule("F1", "a"), rule("F2", "b")]) == []

draft = os.path.join(d, "draft.json")
json.dump([rule("F1", "a"), rule("F2", "b", True)], open(draft, "w"))
today = datetime.date(2026, 11, 7)

s = sc.sign(draft, "v1.0", "asher", today)
assert s["frozen"] and s["signed"] == {"by": "asher", "date": "2026-11-07"} and [r["version"] for r in s["rules"]] == ["v1.0", "v1.0"]
md = open(os.path.join(d, "SCOPE.md")).read()
assert "| F1 | Feature F1 | Rule F1 text |" in md and "security rules: F2" in md and "Signed by asher" in md

for attempt in (lambda: sc.sign(draft, "v1.0", "asher"),                       # cannot be signed twice
                lambda: sc.amend(draft, "CR-001", "asher"),                    # CR still only proposed
                lambda: sc.amend(draft, "CR-404", "asher")):                   # unknown CR
    try:
        attempt(); raise AssertionError("should have refused")
    except SystemExit:
        pass

# The client accepts the quote in writing: the ledger says so, then an amendment is allowed.
v = os.path.join(d, "VERSIONS.md"); t = open(v).read().replace("| proposed |", "| accepted |"); open(v, "w").write(t)
json.dump([rule("F3", "c")], open(draft, "w"))
sc.amend(draft, "CR-001", "asher", today=today)
s = sc.load()
assert s["version"] == "v1.1" and [r["id"] for r in s["rules"]] == ["F1", "F2", "F3"] and s["rules"][2]["version"] == "v1.1"
assert s["amendments"] == [{"cr": "CR-001", "version": "v1.1", "by": "asher", "date": "2026-11-07", "rules": ["F3"]}]
assert "CR-001 -> v1.1" in open(os.path.join(d, "SCOPE.md")).read()
try:
    sc.amend(draft, "CR-001", "asher")                                          # F3 already exists
    raise AssertionError("duplicate rule id must be refused")
except SystemExit:
    pass
assert "frozen" in sc.status() and "F3 (v1.1)" in sc.status()

# CI gate: a frozen contract only grows through an amendment for an accepted change request.
import copy
base, v = sc.load(), os.path.join(d, "VERSIONS.md")
assert sc.verify_change(base, base, v) == []
weak = copy.deepcopy(base); weak["rules"][0]["checks"] = []
assert "F1" in sc.verify_change(base, weak, v)[0]                               # weakened by hand
gone = copy.deepcopy(base); gone["rules"].pop()
assert sc.verify_change(base, gone, v)                                          # removed by hand
extra = copy.deepcopy(base); extra["rules"].append(rule("F9", "z"))
assert "F9" in sc.verify_change(base, extra, v)[0]                              # added without an amendment
unsigned = copy.deepcopy(base); unsigned["signed"] = {"by": "x", "date": "2026-01-01"}
assert sc.verify_change(base, unsigned, v)
ok = copy.deepcopy(extra); ok["amendments"].append({"cr": "CR-001", "version": "v1.1", "by": "a", "date": "d", "rules": ["F9"]})
assert sc.verify_change(base, ok, v) == []
fake = copy.deepcopy(ok); fake["amendments"][-1]["cr"] = "CR-404"
assert sc.verify_change(base, fake, v)                                          # no accepted change request behind it

# New project: blank contract and empty ledgers, the signed one is only replaced on request.
open(os.path.join(d, "DECISIONS.md"), "w").write("# DECISIONS\n<!-- format -->\n2026-11-05 | B1 | x | y | z\n")
open(os.path.join(d, "QUEUE.md"), "w").write("# QUEUE\n\n| Id |\n| --- |\n| B10 |\n")
try:
    sc.new(); raise AssertionError("a signed contract needs the flag")
except SystemExit:
    pass
sc.new(True, today)
s = sc.load()
assert not s["frozen"] and s["rules"] == [] and "Not signed yet" in open(os.path.join(d, "SCOPE.md")).read()
assert "| B10 |" not in open(os.path.join(d, "QUEUE.md")).read() and "| B1 |" not in open(os.path.join(d, "DECISIONS.md")).read()
assert "CR-001" not in open(v).read() and "| MVP |" in open(v).read()
assert sc.verify_change(base, s, v) == []                                       # replacing is a declared act, not a hand edit
json.dump([rule("F1", "a")], open(draft, "w"))
assert sc.sign(draft, "v1.0", "asher", today)["frozen"]                         # and the kickoff starts again
print("ok")
