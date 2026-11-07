"""Compare the Verifier's and the Contradictor's VERDICT lines. Usage: compare.py "<line A>" "<line B>"
Line format: VERDICT R<nn> rule=<F#|none> verdict=<v> severity=<s> security=<yes|no>
Prints AGREE (exit 0) or DISAGREE with the differing fields (exit 1). Malformed line: exit 2."""
import json, re, sys

FIELDS = ("rule", "verdict", "severity", "security")
LINE = re.compile(r"VERDICT (R\d+[a-z]?) rule=(F\d+|none) verdict=(defect|usage|out_of_scope|external|uncertain) "
                  r"severity=(critical|high|medium|low) security=(yes|no)")


def parse(line):
    m = LINE.search(line)
    if not m:
        raise ValueError(f"malformed VERDICT line: {line!r}")
    return m.group(1), dict(zip(FIELDS, m.groups()[1:]))


def compare(a, b):
    (ida, fa), (idb, fb) = parse(a), parse(b)
    if ida != idb:
        raise ValueError(f"different requests: {ida} vs {idb}")
    diff = {k: [fa[k], fb[k]] for k in FIELDS if fa[k] != fb[k]}
    return {"id": ida, "result": "DISAGREE" if diff else "AGREE", "diff": diff, "agreed": fa if not diff else None}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(2)
    try:
        r = compare(*sys.argv[1:])
    except ValueError as e:
        print(e); sys.exit(2)
    print(json.dumps(r, indent=1))
    sys.exit(0 if r["result"] == "AGREE" else 1)
