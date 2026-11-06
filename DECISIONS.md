# DECISIONS
<!-- Planner: one line per human decision. Format: date | id | decision | by | why -->
2026-11-05 | BUG-001 | Deploy now (critical); rollback: redeploy v2.3.0 if payments still fail after 10 min | asher7617 (tech lead, workspace owner) | Critical bug, fix PR ready, dev confirmed
2026-11-06 | B04 | Backlog (out_of_scope, low, no security): CR + quote, not in MVP | asher7617 (tech lead) | Not in SCOPE.md; PDF export needs new route + PDF dependency
2026-11-06 | B10 | Patch lane (defect F5, low, no security): next patch in quiet window | asher7617 (tech lead) | Display bug, non-blocking
2026-11-06 | B11 | Hotfix (defect F6, high, security): deploy after PR; rollback: revert hotfix commit and redeploy previous release; ranked before B10 | asher7617 (tech lead) | Payment/security hole: negative quantity gives negative total
2026-11-06 | B11 | Approved promote staging 4b5ea76 to production; rollback: revert hotfix commit, redeploy previous release | asher (tech lead) | Staging validated F6, security hotfix
