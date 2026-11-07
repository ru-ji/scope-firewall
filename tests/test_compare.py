import sys
sys.path.insert(0, "tools")
from compare import compare

v = "VERDICT R03 rule=F2 verdict=defect severity=high security=no"
r = compare("Verifier says: " + v, v)  # the line may follow free text
assert r["result"] == "AGREE" and r["agreed"]["verdict"] == "defect", r

# Case R03: the hurried reading is "usage" (F1 holds); the contract reading is "defect" (F2 fails).
r = compare("VERDICT R03 rule=F1 verdict=usage severity=low security=no", v)
assert r["result"] == "DISAGREE" and r["diff"] == {"rule": ["F1", "F2"], "verdict": ["usage", "defect"],
                                                    "severity": ["low", "high"]}, r
assert compare(v, v.replace("security=no", "security=yes"))["diff"] == {"security": ["no", "yes"]}

for a, b in ((v, v.replace("R03", "R04")), (v, "VERDICT R03 rule=F2 verdict=broken severity=high security=no"),
             (v, "looks fine to me")):
    try:
        compare(a, b); raise AssertionError((a, b))
    except ValueError:
        pass
print("ok")
