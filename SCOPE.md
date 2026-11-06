# SCOPE: frozen MVP (v1.0)

The signed contract. Every report is judged against this file, and every rule here is executable:
`python3 tools/contract.py check` runs it against the app (rules and checks live in [scope.json](scope.json); F4 is a security rule). Changing this file requires a signed amendment, never a "small addition".

## Rules
| Id | Feature | Required behaviour |
| --- | --- | --- |
| F1 | `POST /pay` | JSON body `{price, qty, coupon?}`. Returns `200 {"total": price * qty * coupon}`. Example: price 10, qty 2, coupon 0.9 → 18.0. |
| F2 | Optional coupon | Missing or `null` coupon means `1` (no discount): price 10, qty 2 → 20. |
| F3 | Coupon upper bound | A coupon above `1` is rejected with `422`; a total is never computed from it. |
| F4 | Coupon lower bound | A coupon of `0` or below is rejected with `422`, so no order is ever free or negative. |

## Out of scope (examples, billed as an amendment)
PDF/CSV export, new payment methods, multi-currency, mobile app, dashboard, any new route.

## Verdict rule (applied by `tools/contract.py verdict <rule>`)
| Situation | Verdict | Who is at fault |
| --- | --- | --- |
| The report maps to a rule and at least one check of that rule fails | **defect** | us |
| The report maps to a rule and every check of that rule passes | **usage** | the client's usage |
| The report maps to no rule | **out_of_scope** | nobody: it is a change request, see [VERSIONS.md](VERSIONS.md) |
| The cause is a third party (CDN, provider) | **external** | watch, no fix |
| The report cannot be mapped or reproduced | **uncertain** | a human decides |
