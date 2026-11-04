---
description: Y2K remediation - updating bank software that stores years as two digits, before the year 2000.
tags: [project, y2k, banking, remediation]
---

# Y2K remediation

Initech's banking clients store years as two digits. In the year 2000, "00" will sort before "99" and interest will be calculated for minus 99 years. This project fixes that.

## Documents

| Document | What it is |
|---|---|
| [plan.md](plan.md) | Scope, approach and milestones |
| [status-report.md](status-report.md) | Weekly status, for Bill |
| [affected-systems.csv](affected-systems.csv) | Every system we have checked |
| [notes/runbook.md](notes/runbook.md) | How to deploy a fix |
| [notes/standups/](notes/standups/) | Daily standup notes |

## Code

| File | Purpose |
|---|---|
| [date_window.py](date_window.py) | The windowing fix: maps two-digit years to four |
| [test_date_window.py](test_date_window.py) | Its tests |
| [find_two_digit_years.sql](find_two_digit_years.sql) | Finds columns that still hold two-digit years |
| [deploy.sh](deploy.sh) | Deploys one fix to one client |

## Team

Peter Gibbons (lead), Michael Bolton, Samir Nagheenanajar. Managed by everyone.
