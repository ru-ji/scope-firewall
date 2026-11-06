# Agents

Source of truth: [switch/bug-team.template.yaml](../switch/bug-team.template.yaml) (import it in Switch Console > Templates).
Real permissions come from addressing rules and the account's access, not from these texts.

| Agent | Provider | Room | Role | Access |
| --- | --- | --- | --- | --- |
| Reception | A | #support | Masks secrets, restates, asks missing questions, classifies, drafts the client reply | No code, no logs; addressable by anyone |
| Verifier | A: Claude Code | #investigation | Maps the report to a SCOPE.md rule, runs `contract.py verdict`, proposes severity | Read-only + `bugs/<id>.md` |
| Contradictor | B: Codex (GPT) | #cross-check (alone) | Gets the sheet only, maps it independently, runs the contract itself, posts its VERDICT line | Read-only |
| Fixer | A | #investigation | Branch `fix/<id>` or `build/<version>`, target rules pass and nothing regresses in `contract.py check`, PR | Branch write only |
| Planner | A | #planning | Kickoff and amendments (`scope.py`), `compare.py`, `triage_lane.py`, `plan_window.py`, `priorities.py`, `versions.py`, `envs.py`, DECISIONS.md | Writes the ledgers and, after a human signature, the contract |

Shared context: `bugs/<id>.md` (from `bugs/TEMPLATE.md`), `SCOPE.md` (frozen contract), `VERSIONS.md` (change requests).
