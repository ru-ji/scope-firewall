# ENVIRONMENTS: what runs where

Written by `tools/envs.py`. Production only receives a commit from staging that breaks no rule production passes, with a named human approval.

| Time | Env | Commit | Contract | Failing | By |
| --- | --- | --- | --- | --- | --- |
| 2026-11-06 15:02 | staging | 4b5ea76 | 10/11 | F5 | Planner |
| 2026-11-06 15:03 | production | 4b5ea76 | 10/11 | F5 | approved by asher |
