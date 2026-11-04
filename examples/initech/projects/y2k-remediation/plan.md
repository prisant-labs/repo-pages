---
description: Plan for the Y2K remediation - scope, the windowing approach, and milestones up to the end of December.
tags: [project, y2k, plan]
---

# Y2K remediation plan

## Scope

All client systems that store or compare dates. See [affected-systems.csv](affected-systems.csv) for the list, which grows each week.

## Approach

We use **date windowing** instead of expanding every field to four digits.

1. Pick a pivot year. We use 50.
2. Two-digit years from 00 to 49 become 2000 to 2049.
3. Two-digit years from 50 to 99 become 1950 to 1999.

This changes code, not data, so no database has to be rebuilt. It will need revisiting in 2049. That is someone else's project.

```python
def expand_year(yy: int, pivot: int = 50) -> int:
    return 2000 + yy if yy < pivot else 1900 + yy
```

The full version, with validation, is in [date_window.py](date_window.py).

## Milestones

| Milestone | Target | State |
|---|---|---|
| Inventory every system | Week 2 | Done |
| Fix and test the ledger | Week 5 | Done |
| Fix and test interest calculation | Week 7 | In progress |
| Client sign-off | Week 9 | Not started |
| Code freeze | December 1 | Not started |

## Risks

| Risk | Mitigation |
|---|---|
| Hidden two-digit years in reports | Run [find_two_digit_years.sql](find_two_digit_years.sql) on every schema |
| Managers asking for status | One [status report](status-report.md), sent weekly |
| Saturday work | None known |
