# DECISIONS
<!-- Planner: one line per human decision. Format: date | id | decision | by | why -->
2026-11-05 | BUG-001 | Deploy now (critical); rollback: redeploy v2.3.0 if payments still fail after 10 min | asher7617 (tech lead, workspace owner) | Critical bug, fix PR ready, dev confirmed
2026-11-06 | B01 | verdict confirmed: rule=F2 defect critical security=no, lane=hotfix | asher (tech lead) | Verifier and Contradictor agree
2026-11-06 | B01 | hotfix deploy approved (PR ru-ji/scope-firewall#1, rollback: revert hotfix commit + redeploy previous release) | asher (tech lead) | critical F2 defect, PR green (contract 8/8, tests pass)
2026-11-06 | B04 | out_of_scope, backlog lane, CR-001 created (effort L), quote drafted | asher (tech lead) | PDF order export not in SCOPE.md
2026-11-06 | B03 | patch lane approved, window 03:30, rollback: revert patch commit | asher (tech lead) | F3 defect high, non-blocking; now 4000 req/h vs 300 in window
