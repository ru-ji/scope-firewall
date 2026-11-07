# Agents

Source of truth: [switch/scope-firewall.template.yaml](../switch/scope-firewall.template.yaml) (import it in Switch Console > Templates).
Real permissions come from addressing rules and the account's access, not from these texts.

| Agent | Provider | Room | Role | Access |
| --- | --- | --- | --- | --- |
| Reception | A | #client-requests | Masks secrets, splits a message into one sheet per request, asks missing questions, classifies, drafts the client reply | No code, no logs; addressable by anyone |
| Verifier | A: Claude Code | #verification | Maps the report to a SCOPE.md rule, runs `contract.py verdict`, proposes severity | Read-only + `cases/<id>.md` |
| Contradictor | B: Codex (GPT) | #cross-check (alone) | Gets the sheet only, maps it independently, runs the contract itself, posts its VERDICT line | Read-only |
| Fixer | A | #verification | Branch `fix/<id>` or `build/<version>`, target rules pass and nothing regresses in `contract.py check`, PR | Branch write only |
| Planner | A | #planning | Kickoff and amendments (`scope.py`), `compare.py`, `triage_lane.py`, `plan_window.py`, `priorities.py`, `versions.py`, `envs.py`, DECISIONS.md | Writes the ledgers and, after a human signature, the contract |

Shared context: `cases/<id>.md` (from `cases/TEMPLATE.md`), `SCOPE.md` (the signed contract), `VERSIONS.md` (change requests).
