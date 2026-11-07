# Scope Firewall: reference

Rules behind the workflow. The story, setup and demo are in the [README](README.md).

## Verdicts

Applied by `tools/contract.py`, from real requests to the app, never from model opinion.

| Situation | Verdict |
| --- | --- |
| Request maps to a rule, at least one check of that rule fails | `defect` |
| Request maps to a rule, every check passes | `usage` |
| Request maps to no rule | `out_of_scope` |
| Third-party cause | `external` |
| Cannot be mapped or reproduced | `uncertain` |

## Exits

Applied by `tools/triage_lane.py`.

| Verdict | Severity or flag | Exit | What happens |
| --- | --- | --- | --- |
| defect | security or critical | `hotfix` | PR, tech lead approves, deploy now with a rollback plan |
| defect | high, medium, low | `patch` | Same PR, batched, deployed in the quiet window from `tools/plan_window.py` |
| usage | any | `reply` | Draft reply sent by a human; no code |
| out_of_scope | any | `backlog` | Change request and quote in VERSIONS.md; the contract changes only if the client accepts |
| external | any | `watch` | Monitor, no fix |
| uncertain | any | `human` | A human decides |

Severity: critical = payments fail for most clients; high = a wrong amount is charged or money is lost; medium = degraded with a workaround; low = cosmetic, usage, out of scope or uncertain.

## Ids

`R<nn>` is one client request. A message that mixes several requests becomes `R<nn>a`, `R<nn>b`: each has its own sheet, verdict and exit. `CR-<nnn>` is a change request; `F<n>` is a contract rule.

## Rooms

| Room | Agents | Content |
| --- | --- | --- |
| #client-requests | Reception | Pasted client messages, sheets, draft replies. The only room with untrusted text: no agent there has repo access |
| #verification | Verifier, Fixer, plus Reception and Planner | Contract output, VERDICT lines, builds, PRs |
| #cross-check | Contradictor, plus Reception and Planner | The same sheet, blind; the second VERDICT line |
| #planning | Planner | Kickoff, contract, plan, approvals, change requests, environments |

## Security

- Protection comes from real permissions, not prompts: Switch does not inspect tool calls.
- Reception answers anyone because it has no access; every other agent answers only its owner and its agents.
- Agents inherit their owner's access: run them under a dedicated account with access to this repository only.
- Keep Bypass permissions off. Turn off OpenCode Auto mode, which approves every request.
- Reception masks passwords, tokens, emails and IPs before anything is posted.
- Reception hands a sheet over only on a teammate's `GO`, and it has no repo access. The two agents that receive it are read-only.
- The Planner reads the two verification rooms only to fetch VERDICT lines, and passes nothing between them until both exist.
- Mattermost adds agents to its default channels (Town Square, Off-Topic). Nothing about a request is posted there.
- No agent merges, deploys on its own or messages the client.

## Sources

- [Hackathon page](https://www.wemakedevs.org/hackathons/switch), [Switch repository](https://github.com/sandbox-quantum/switch)
- [Agent settings](https://docs.switchagents.ai/switch-rooms/getting-started/agent-settings.md), [Identity and access](https://docs.switchagents.ai/switch-rooms/internals/identity-and-access.md), [Shared context](https://docs.switchagents.ai/switch-rooms/using/shared-context.md)
- [Room templates](https://github.com/sandbox-quantum/switch/blob/main/docs/TEMPLATES.md), [Working safely with agents](https://docs.switchagents.ai/switch-rooms/resources/working-safely-with-agents.md)
