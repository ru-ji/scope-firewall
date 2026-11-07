# DECISIONS
<!-- Planner: one line per human decision. Format: date | id | decision | by | why -->
2026-11-05 | R01 | Deploy now (critical); rollback: redeploy the previous release if payments still fail after 10 min | asher (tech lead, workspace owner) | Critical bug, fix PR ready, dev confirmed
2026-11-06 | R04 | Backlog (out_of_scope, low, no security): CR + quote, not in MVP | asher (tech lead) | Not in SCOPE.md; PDF export needs new route + PDF dependency
2026-11-06 | R10 | Patch lane (defect F5, low, no security): next patch in quiet window | asher (tech lead) | Display bug, non-blocking
2026-11-06 | R11 | Hotfix (defect F6, high, security): deploy after PR; rollback: revert hotfix commit and redeploy previous release; ranked before R10 | asher (tech lead) | Payment/security hole: negative quantity gives negative total
2026-11-06 | R11 | Approved promote staging 4b5ea76 to production; rollback: revert hotfix commit, redeploy previous release | asher (tech lead) | Staging validated F6, security hotfix
