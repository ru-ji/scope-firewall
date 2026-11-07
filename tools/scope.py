"""Contract lifecycle. scope.json is the source of truth; SCOPE.md is regenerated from it, so they cannot drift.

Usage:
  scope.py new [--replace-signed]                        new project: blank contract and empty ledgers (git keeps the old
                                                         ones); a signed contract is only replaced with the flag
  scope.py sign <draft.json> <version> "<signed by>"     kickoff: validate the drafted rules, write them to scope.json,
                                                         freeze the version and regenerate SCOPE.md
  scope.py amend <draft.json> <CR-id> "<signed by>"      evolution: add rules for a change request the client ACCEPTED
                                                         in VERSIONS.md; the contract moves to that request's version
  scope.py status                                        version, frozen or not, rules, amendments
  scope.py verify-change <base scope.json>               CI gate: compare with the base commit; a frozen contract only
                                                         grows through an amendment for an accepted change request

A draft is a JSON list of rules: {"id": "F1", "feature": "...", "security": false, "text": "...", "checks": [
  {"name": "...", "body": {...}, "status": 200, "total": 20, "fields": {...}, "present": [...], "path": "/x"}]}
Once frozen, the contract only changes through `amend`, never by hand.
"""
import datetime, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SCOPE_JSON = os.environ.get("SCOPE_FILE") or os.path.join(ROOT, "scope.json")
SCOPE_MD = os.path.join(os.path.dirname(SCOPE_JSON), "SCOPE.md")
VERSIONS_MD = os.path.join(os.path.dirname(SCOPE_JSON), "VERSIONS.md")


def validate(rules, taken_ids=(), taken_checks=()):
    """Return a list of problems; empty means the draft is a valid contract fragment."""
    errs, ids, names = [], set(taken_ids), set(taken_checks)
    if not isinstance(rules, list) or not rules:
        return ["the draft must be a non-empty JSON list of rules"]
    for r in rules:
        rid = r.get("id") if isinstance(r, dict) else None
        if not isinstance(rid, str) or not re.fullmatch(r"F\d+", rid):
            errs.append(f"rule id must look like F7, got {rid!r}")
            continue
        if rid in ids:
            errs.append(f"{rid}: id already used")
        ids.add(rid)
        for k in ("feature", "text"):
            if not isinstance(r.get(k), str) or not r[k].strip() or "|" in r[k] or "\n" in r[k]:
                errs.append(f"{rid}: {k} must be one line of text without '|'")
        if not isinstance(r.get("security"), bool):
            errs.append(f"{rid}: security must be true or false")
        checks = r.get("checks")
        if not isinstance(checks, list) or not checks:
            errs.append(f"{rid}: at least one executable check is required")
            continue
        for c in checks:
            n = c.get("name") if isinstance(c, dict) else None
            if not isinstance(n, str) or not n.strip():
                errs.append(f"{rid}: every check needs a name")
                continue
            if n in names:
                errs.append(f"{rid}: check name {n!r} already used")
            names.add(n)
            if not isinstance(c.get("body"), dict):
                errs.append(f"{rid}/{n}: body must be a JSON object")
            if not isinstance(c.get("status"), int):
                errs.append(f"{rid}/{n}: status must be an HTTP status number")
            if "total" in c and c["total"] is not None and not isinstance(c["total"], (int, float)):
                errs.append(f"{rid}/{n}: total must be a number or null")
            if "fields" in c and not isinstance(c["fields"], dict):
                errs.append(f"{rid}/{n}: fields must be an object")
            if "present" in c and not (isinstance(c["present"], list) and all(isinstance(x, str) for x in c["present"])):
                errs.append(f"{rid}/{n}: present must be a list of field names")
            if "path" in c and not (isinstance(c["path"], str) and c["path"].startswith("/")):
                errs.append(f"{rid}/{n}: path must start with '/'")
    return errs


def load():
    return json.load(open(SCOPE_JSON))


def render(scope):
    rows = "\n".join(f"| {r['id']} | {r['feature']} | {r['text']} |" for r in scope["rules"]) or "| none yet | | |"
    sec = ", ".join(r["id"] for r in scope["rules"] if r["security"]) or "none"
    amend = "; ".join(f"{a['cr']} -> {a['version']} ({a['by']}, {a['date']})" for a in scope.get("amendments", [])) or "none"
    sig = scope.get("signed")
    signed = f"Signed by {sig['by']} on {sig['date']}." if sig else "Not signed yet: the kickoff has not produced a contract."
    return f"""# SCOPE: contract {scope['version']}{' (frozen)' if scope.get('frozen') else ''}

The signed contract. Every report is judged against this file, and every rule here is executable:
`python3 tools/contract.py check` runs it against the app (rules and checks live in [scope.json](scope.json); security rules: {sec}).
It changes only through `python3 tools/scope.py amend`, for a change request the client accepted: never a "small addition".

{signed} Amendments: {amend}.

## Rules
| Id | Feature | Required behaviour |
| --- | --- | --- |
{rows}

## Out of scope
Anything no rule covers. It is never done for free: it becomes a change request with a quote in [VERSIONS.md](VERSIONS.md).

## Verdict rule (applied by `tools/contract.py verdict <rule>`)
| Situation | Verdict | Who is at fault |
| --- | --- | --- |
| The report maps to a rule and at least one check of that rule fails | **defect** | us |
| The report maps to a rule and every check of that rule passes | **usage** | the client's usage |
| The report maps to no rule | **out_of_scope** | nobody: it is a change request, see [VERSIONS.md](VERSIONS.md) |
| The cause is a third party (CDN, provider) | **external** | watch, no fix |
| The report cannot be mapped or reproduced | **uncertain** | a human decides |
"""


def save(scope):
    json.dump(scope, open(SCOPE_JSON, "w"), ensure_ascii=False, indent=1)
    open(SCOPE_JSON, "a").write("\n")
    open(SCOPE_MD, "w").write(render(scope))


def _draft(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError) as e:
        raise SystemExit(f"REFUSED: cannot read the draft {path}: {e}")


def _taken(scope):
    return [r["id"] for r in scope["rules"]], [c["name"] for r in scope["rules"] for c in r["checks"]]


def _clear(path, tail=""):
    """Empty a ledger, keeping its header (everything down to the table separator or the format comment)."""
    if os.path.exists(path):
        lines = open(path).read().splitlines(keepends=True)
        last = max((i for i, l in enumerate(lines) if l.startswith(("| ---", "<!--"))), default=-1)
        open(path, "w").write("".join(lines[:last + 1]) + tail)


def new(replace_signed=False, today=None):
    scope = load()
    if scope.get("frozen") and not replace_signed:
        raise SystemExit(f"REFUSED: {scope['version']} is signed; replacing it for a new project needs --replace-signed")
    save({"version": "v0", "endpoint": scope["endpoint"], "app": scope["app"], "frozen": False, "rules": [],
          "replaced": (today or datetime.date.today()).isoformat()})
    base = os.path.dirname(SCOPE_JSON)
    for name in ("QUEUE.md", "ENVIRONMENTS.md", "DECISIONS.md"):
        _clear(os.path.join(base, name))
    _clear(VERSIONS_MD, "| v1.0 | MVP | signed contract | every rule of SCOPE.md | n/a | see SCOPE.md | accepted |\n")
    open(os.path.join(base, "schedule.json"), "w").write("{}\n")


def sign(draft_path, version, by, today=None):
    scope = load()
    if scope.get("frozen"):
        raise SystemExit(f"REFUSED: {scope['version']} is already signed and frozen; use `amend` for an accepted change request")
    if not re.fullmatch(r"v\d+\.\d+", version) or not by.strip():
        raise SystemExit("REFUSED: give a version like v1.0 and the name of the signer")
    rules = _draft(draft_path)
    errs = validate(rules, *_taken(scope))
    if errs:
        raise SystemExit("REFUSED:\n- " + "\n- ".join(errs))
    scope["rules"] += [{**r, "version": version} for r in rules]
    scope.update(version=version, frozen=True, signed={"by": by.strip(), "date": (today or datetime.date.today()).isoformat()})
    save(scope)
    return scope


def accepted_cr(cr_id, path=None):
    """The (version, status) of a change request row in VERSIONS.md, or None."""
    path = path or VERSIONS_MD
    if not os.path.exists(path):
        return None
    for line in open(path):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 7 and c[1] == cr_id:
            return c[0], c[6]
    return None


def amend(draft_path, cr_id, by, versions_path=None, today=None):
    scope = load()
    if not scope.get("frozen"):
        raise SystemExit("REFUSED: nothing to amend, the contract is not signed yet (use `sign`)")
    cr = accepted_cr(cr_id, versions_path)
    if cr is None:
        raise SystemExit(f"REFUSED: {cr_id} is not in VERSIONS.md")
    if cr[1] not in ("accepted", "delivered"):
        raise SystemExit(f"REFUSED: {cr_id} is {cr[1]}, the client has not accepted the quote (status must be accepted)")
    if not by.strip():
        raise SystemExit("REFUSED: the name of the signer is required")
    rules = _draft(draft_path)
    errs = validate(rules, *_taken(scope))
    if errs:
        raise SystemExit("REFUSED:\n- " + "\n- ".join(errs))
    scope["rules"] += [{**r, "version": cr[0]} for r in rules]
    scope["version"] = cr[0]
    scope.setdefault("amendments", []).append({"cr": cr_id, "version": cr[0], "by": by.strip(),
                                               "date": (today or datetime.date.today()).isoformat(),
                                               "rules": [r["id"] for r in rules]})
    save(scope)
    return scope


def verify_change(base, head, versions_path=None):
    """Problems with going from the base contract to the head one; empty means the change is legitimate."""
    if not base.get("frozen"):
        return []
    # ponytail: `new` is trusted on its "replaced" date, so a PR that sets it is only caught by the human review
    if head.get("replaced") and head["replaced"] != base.get("replaced"):
        return []
    errs = []
    if not head.get("frozen") or head.get("signed") != base.get("signed"):
        errs.append("the signature or the freeze changed")
    rules, kept = {r["id"]: r for r in head["rules"]}, base.get("amendments", [])
    errs += [f"{r['id']} was changed or removed in a frozen contract" for r in base["rules"] if rules.get(r["id"]) != r]
    if head.get("amendments", [])[:len(kept)] != kept:
        errs.append("a past amendment was changed")
    added = head.get("amendments", [])[len(kept):]
    covered = {i for a in added for i in a["rules"]}
    errs += [f"{i} was added without an amendment" for i in rules if i not in {r["id"] for r in base["rules"]} | covered]
    for a in added:
        cr = accepted_cr(a["cr"], versions_path)
        if cr is None or cr[1] not in ("accepted", "delivered"):
            errs.append(f"{a['cr']} was not accepted by the client")
    return errs


def status():
    s = load()
    sig = s.get("signed")
    out = [f"contract {s['version']}, {'frozen' if s.get('frozen') else 'NOT signed'}"
           + (f", signed by {sig['by']} on {sig['date']}" if sig else ""),
           f"{len(s['rules'])} rules: " + (", ".join(f"{r['id']} ({r.get('version', 'v1.0')})" for r in s["rules"]) or "none")]
    out += [f"amendment {a['cr']} -> {a['version']} by {a['by']}: {', '.join(a['rules'])}" for a in s.get("amendments", [])]
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["new"] and a[1:] in ([], ["--replace-signed"]):
        new(bool(a[1:]))
        print("blank contract, empty ledgers. Next: KICKOFF with the client brief.")
    elif a[:1] == ["verify-change"] and len(a) == 2:
        errs = verify_change(json.load(open(a[1])), load())
        if errs:
            raise SystemExit("REFUSED:\n- " + "\n- ".join(errs))
        print("contract change is legitimate")
    elif a[:1] == ["sign"] and len(a) == 4:
        s = sign(a[1], a[2], a[3])
        print(f"signed {s['version']}: {len(s['rules'])} rules, frozen. SCOPE.md regenerated.")
    elif a[:1] == ["amend"] and len(a) == 4:
        s = amend(a[1], a[2], a[3])
        print(f"amended: contract is now {s['version']}, {len(s['rules'])} rules. SCOPE.md regenerated.")
    elif a[:1] == ["status"]:
        print(status())
    else:
        print(__doc__)
        sys.exit(2)
