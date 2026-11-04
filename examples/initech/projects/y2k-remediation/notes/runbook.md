---
description: Runbook for deploying a Y2K fix to a client, and what to do if it goes wrong.
tags: [project, y2k, runbook, deploy]
---

# Y2K deploy runbook

## Before

- [ ] Tests pass: `python3 -m unittest test_date_window`
- [ ] TPS report written, with the new cover sheet
- [ ] Client contact told the window and the time

## Deploy

```bash
DRY_RUN=0 ./deploy.sh first-mutual interest-calc
```

## After

1. Run the client's end-of-day batch in their test region.
2. Compare three statements against last month's.
3. File the TPS report.

## If it goes wrong

| Symptom | Likely cause | What to do |
|---|---|---|
| Interest for minus 99 years | The fix did not deploy | Check the release folder, deploy again |
| Fractions of a cent missing | Not this project | See [the rounding incident](../../rounding-incident/postmortem.md) |
| Printer says PC LOAD LETTER | The printer | See [the printer report](../../../teams/software/printer-incident-report.md) |
