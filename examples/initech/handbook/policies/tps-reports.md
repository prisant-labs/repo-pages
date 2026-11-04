---
description: The TPS reports policy - what goes in a report, when it is due, and the cover sheet that must go on top.
tags: [policy, tps, reports, cover-sheet]
---

# TPS reports

Testing Procedure Specification reports record what was tested, how, and by whom. Every software change gets one.

## When they are due

| Report | Due |
|---|---|
| Weekly TPS | Friday, 5:00 PM |
| Release TPS | Before the release, not after |
| Corrected TPS | Whenever someone notices the cover sheet is missing |

## The cover sheet

Every TPS report gets the **new** cover sheet. The old cover sheet was retired. See [the memo](../../memos/from-bill-lumbergh/new-cover-sheets.md) for why, and the [form itself](../../forms/tps-cover-sheet.pdf).

If you forget the cover sheet, you will hear about it. Usually more than once. Usually from more than one person.

### Required fields

1. Project code
2. Report date
3. Tester
4. Number of test cases, run and passed
5. Manager initials (all managers)

### What not to do

- Do not staple the cover sheet to the back.
- Do not write "see attached" on the cover sheet. The cover sheet is the attached.
- Do not use the old cover sheet, even if you have a stack of them.

## Volume

See [data/tps-reports-filed.csv](../../data/tps-reports-filed.csv) for every report filed this quarter, and which ones had a cover sheet.

## Automation

There is a [script](../../tools/tps_report.py) that fills in the cover sheet fields from a test run. Using it is encouraged. You still have to print it.
