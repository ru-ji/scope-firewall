"""Environments: staging and production, each running one exact commit of the app. Writes ENVIRONMENTS.md.

Usage:
  envs.py deploy staging <git ref>       (e.g. origin/main) fetch, check out the commit, run it on the staging port, replay the contract
  envs.py promote <approved by>          ship to production the commit that is on staging; refused if staging fails
                                         any contract rule that production passes (no regression), or without a
                                         named human approval
  envs.py status                         which commit runs where, and its last contract result

Production is never deployed from a git ref, only promoted from staging. A hotfix can ship while a minor bug
still waits for its patch (that rule already failed in production), but nothing that works today can break.
"""
import datetime, json, os, signal, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contract import run as contract_run

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LEDGER = os.path.join(ROOT, "ENVIRONMENTS.md")
WORK = os.path.join(ROOT, ".envs")
PORTS = {"staging": 8081, "production": 8080}
COLS = ["Time", "Env", "Commit", "Contract", "Failing", "By"]
HEADER = ("# ENVIRONMENTS: what runs where\n\nWritten by `tools/envs.py`. Production only receives a commit from "
          "staging that breaks no rule production passes, with a named human approval.\n\n| " + " | ".join(COLS) + " |\n|"
          + " --- |" * len(COLS) + "\n")


def load(path=LEDGER):
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| 20") and len(cells) == len(COLS):
            rows.append(dict(zip(COLS, cells)))
    return rows


def record(env, commit, passed, total, failing, by, path=LEDGER):
    rows = load(path) + [{"Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "Env": env, "Commit": commit,
                          "Contract": f"{passed}/{total}", "Failing": ", ".join(failing) or "-", "By": by}]
    with open(path, "w") as f:
        f.write(HEADER + "".join("| " + " | ".join(r[c] for c in COLS) + " |\n" for r in rows))


def current(env, rows):
    hits = [r for r in rows if r["Env"] == env]
    return hits[-1] if hits else None


def _failing(row):
    return set() if row["Failing"] == "-" else set(row["Failing"].split(", "))


def can_promote(rows, approved_by):
    """Pure rule, tested: returns (ok, reason, commit). No regression: staging may only fail rules production
    already fails. The first promotion sets the production baseline."""
    if not approved_by.strip():
        return False, "a named human approval is required", None
    st, prod = current("staging", rows), current("production", rows)
    if st is None:
        return False, "nothing is deployed on staging", None
    if prod is not None:
        regressions = sorted(_failing(st) - _failing(prod))
        if regressions:
            return False, f"regression on staging {st['Commit']}: {', '.join(regressions)} works in production", st["Commit"]
        fixed = sorted(_failing(prod) - _failing(st))
        return True, f"staging {st['Commit']} fixes {', '.join(fixed) or 'nothing new'}, no regression", st["Commit"]
    return True, f"first production baseline: {st['Commit']} ({st['Contract']})", st["Commit"]


def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], check=True, capture_output=True, text=True).stdout.strip()


def _start(env, commit):
    """Check out `commit` in .envs/<env> and run its app on the env's port (replacing what ran there)."""
    os.makedirs(WORK, exist_ok=True)
    pidfile, tree = os.path.join(WORK, f"{env}.pid"), os.path.join(WORK, env)
    if os.path.exists(pidfile):
        try:
            os.kill(int(open(pidfile).read()), signal.SIGTERM)
            time.sleep(0.5)
        except (ProcessLookupError, ValueError):
            pass
    if os.path.exists(tree):
        _git("worktree", "remove", "--force", tree)
    _git("worktree", "add", "--force", "--detach", tree, commit)
    log = open(os.path.join(WORK, f"{env}.log"), "w")
    p = subprocess.Popen([sys.executable, os.path.join(tree, "demo-app", "app.py")], cwd=tree, stdout=log,
                         stderr=log, env={**os.environ, "PORT": str(PORTS[env])}, start_new_session=True)
    open(pidfile, "w").write(str(p.pid))
    url = f"http://127.0.0.1:{PORTS[env]}"
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=0.5)
        except urllib.error.HTTPError:
            break  # the server answers (any HTTP status means it is up)
        except OSError:
            time.sleep(0.25)
    return url


def _check(url):
    res = contract_run(url)
    return sum(c["pass"] for c in res), len(res), sorted({c["rule"] for c in res if not c["pass"]})


def deploy_staging(ref, by="Planner"):
    subprocess.run(["git", "-C", ROOT, "fetch", "-q", "origin"], capture_output=True)  # see what was just merged
    commit = _git("rev-parse", "--short", ref)
    passed, total, failed = _check(_start("staging", commit))
    record("staging", commit, passed, total, failed, by)
    return commit, passed, total, failed


def promote(approved_by):
    ok, reason, commit = can_promote(load(), approved_by)
    if not ok:
        raise SystemExit(f"REFUSED: {reason}")
    passed, total, failed = _check(_start("production", commit))
    record("production", commit, passed, total, failed, f"approved by {approved_by}")
    return commit, passed, total, failed


def status():
    rows = load()
    out = []
    for env in PORTS:
        r = current(env, rows)
        out.append(f"{env:<10} port {PORTS[env]}  " + (f"commit {r['Commit']}  contract {r['Contract']}  failing {r['Failing']}  ({r['By']}, {r['Time']})"
                                                       if r else "nothing deployed"))
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:2] == ["deploy", "staging"] and len(a) == 3:
        c, p, t, f = deploy_staging(a[2])
        print(f"staging <- {c}: contract {p}/{t}, failing: {', '.join(f) or 'none'}")
        print(can_promote(load(), "check")[1])
    elif a[:1] == ["deploy"]:
        raise SystemExit("REFUSED: production is never deployed directly; use `envs.py promote <approved by>`")
    elif a[:1] == ["promote"] and len(a) == 2:
        c, p, t, f = promote(a[1])
        print(f"production <- {c}: contract {p}/{t}, failing: {', '.join(f) or 'none'}")
    elif a[:1] == ["status"]:
        print(status())
    else:
        print(__doc__)
        sys.exit(2)
