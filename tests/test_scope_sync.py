"""SCOPE.md (what the client signed) and scope.json (what the contract checker runs) must say the same thing."""
import json, re

scope = json.load(open("scope.json"))
md = open("SCOPE.md").read()
rows = dict(re.findall(r"^\| (F\d+) \| .*? \| (.*) \|$", md, re.M))
ids = [r["id"] for r in scope["rules"]]
assert list(rows) == ids, (list(rows), ids)
for r in scope["rules"]:
    assert rows[r["id"]] == r["text"], (r["id"], rows[r["id"]], r["text"])
    assert r["checks"], f"{r['id']} has no executable check"
assert scope["version"] in md
print("ok")
