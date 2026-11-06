"""Planner: change-request ledger in VERSIONS.md. SCOPE.md is never touched.

Usage:
  versions.py add "<request>" <S|M|L> "<origin>" "<files touched>" [version]   -> prints the new CR id and a draft quote
  versions.py status <CR-id> <proposed|quote-sent|accepted|rejected|delivered>
"""
import re, sys

PATH = "VERSIONS.md"
EFFORT = {"S": "under 0.5 day", "M": "0.5 to 2 days", "L": "over 2 days"}
STATUSES = ("proposed", "quote-sent", "accepted", "rejected", "delivered")


def _cell(s):
    s = " ".join(str(s).split())
    if not s:
        raise SystemExit("empty field")
    return s.replace("|", "/")


def add(request, effort, origin, files, version="v1.1", path=PATH):
    if effort not in EFFORT:
        raise SystemExit(f"effort must be one of {list(EFFORT)}")
    if not re.fullmatch(r"v\d+\.\d+", version) or version == "v1.0":
        raise SystemExit("version must look like v1.1 and can never be v1.0 (frozen MVP)")
    text = open(path).read()
    n = max([int(x) for x in re.findall(r"\| CR-(\d+) \|", text)] or [0]) + 1
    cid = f"CR-{n:03d}"
    row = f"| {version} | {cid} | {_cell(origin)} | {_cell(request)} | {effort} | {_cell(files)} | proposed |\n"
    open(path, "a").write(row if text.endswith("\n") else "\n" + row)
    quote = (f"Quote draft {cid} ({version}): \"{_cell(request)}\" is not part of the signed MVP (SCOPE.md). "
             f"Estimated effort {effort} ({EFFORT[effort]}). It will ship in {version} after your written approval, "
             f"billed separately from the MVP. The MVP delivery date is unchanged.")
    return cid, quote


def status(cid, new, path=PATH):
    if new not in STATUSES:
        raise SystemExit(f"status must be one of {STATUSES}")
    lines = open(path).read().splitlines(keepends=True)
    hit = [i for i, l in enumerate(lines) if l.startswith("|") and f"| {cid} |" in l]
    if len(hit) != 1:
        raise SystemExit(f"{cid} not found")
    cells = lines[hit[0]].rstrip("\n").split("|")
    cells[-2] = f" {new} "
    lines[hit[0]] = "|".join(cells) + "\n"
    open(path, "w").writelines(lines)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["add"] and len(a) in (5, 6):
        cid, quote = add(*a[1:])
        print(cid)
        print(quote)
    elif a[:1] == ["status"] and len(a) == 3:
        status(a[1], a[2])
        print(f"{a[1]} -> {a[2]}")
    else:
        print(__doc__)
        sys.exit(2)
