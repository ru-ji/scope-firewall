# VERSIONS: release ledger and change requests

The MVP (v1.0, see [SCOPE.md](SCOPE.md)) is frozen. A request outside the scope never enters the MVP: it becomes a row
below, written by `tools/versions.py`, with an effort estimate and a quote the client must approve. It is billed separately.

Effort: S (under 0.5 day), M (0.5 to 2 days), L (over 2 days), estimated from the files the change would touch.
Status: proposed | quote-sent | accepted | rejected | delivered.

| Version | Id | Origin (channel, date) | Request | Effort | Files touched | Status |
| --- | --- | --- | --- | --- | --- | --- |
| v1.0 | MVP | signed contract | rules F1-F6 of SCOPE.md | n/a | demo-app/app.py | delivered |
| v1.1 | CR-001 | Slack, 2026-11-06 | PDF export of orders for accounting | L | demo-app/app.py (new export route + PDF library) | proposed |
