# Live run: Claude Code vs Codex, blind (2026-11-06)

Each agent got the same sheet and its own instructions from `switch/bug-team.template.yaml`, in parallel, without seeing the other.
Verifier: `claude -p` (Claude Code). Contradictor: `codex exec -s read-only` (Codex CLI 0.166.0, ChatGPT login).
The VERDICT lines below are copied verbatim, and `tools/compare.py` gives the result.

| Case | Verifier (Claude Code) | Contradictor (Codex / GPT) | compare.py |
| --- | --- | --- | --- |
| B03 coupon=10 "my fault" | `rule=F3 verdict=defect severity=high security=no` | `rule=F3 verdict=defect severity=high security=no` | AGREE |
| B04 PDF export | `rule=none verdict=out_of_scope severity=low security=no` | `rule=none verdict=out_of_scope severity=low security=no` | AGREE |
| B01 "can't pay", first run | `rule=F2 verdict=defect severity=critical security=no` | `rule=F1 verdict=usage severity=low security=no` | **DISAGREE** |
| B01 after the fix below (2 runs) | same | `rule=F2 verdict=defect severity=critical security=no` | AGREE, 2/2 |

## What the live runs changed

1. **Codex's sandbox blocks the network**, even to localhost. Its first run could not reach the app and answered `uncertain`.
   Fix: `contract.py` now runs the app's HTTP handler in-process by default (`--local`). It needs no server and no network, and its results are identical to the real HTTP run (`tests/test_contract.py` asserts that). CI still checks over real HTTP.
2. **One rule bundled three problems**, so the security flag was a matter of opinion: Claude flagged B03 as a security issue because the same rule also covered free orders.
   Fix: the coupon rules are split into F2 (missing coupon), F3 (above 1) and F4 (0 or below). F4 is marked `security: true` in `scope.json`, and agents copy the flag from the tool output.
3. **The blind Contradictor had too little evidence.** It was only allowed the client message and SCOPE.md, so it mapped the vague "can't pay" to F1, which passes, and answered `usage`. `compare.py` caught the mismatch and sent it to a human, as designed.
   Fix: the Contradictor may now also read evidence (`data/app.log`, `contract.py check`), but still never the Verifier's reasoning. B01 now agrees in 2 out of 2 runs.

Not run live: Reception (B05 injection, B06 secret masking) and the Planner. Their scripts are covered by the test suite. The agents' behaviour inside Switch is shown in the demo video.
