---
description: Blameless postmortem for the ledger rounding incident, where a decimal point in the wrong place moved far more money than intended.
tags: [project, postmortem, incident, ledger, rounding]
---

# Postmortem: ledger rounding incident

**Severity:** high. **Status:** closed. **Owner:** Michael Bolton.

This is a blameless postmortem. Several people have asked that it stay that way.

## Summary

A change to the ledger rounding module put a decimal point in the wrong place. Instead of moving fractions of a cent, as designed, it moved noticeably more than that over a weekend. The difference was found, the money was returned, and the change was removed.

## Timeline

| When | What happened |
|---|---|
| Friday evening | Change deployed with the Y2K ledger fix |
| Saturday | Batch runs. Nobody is in the office. Officially |
| Monday 9:00 | An account balance is noticed. It has too many digits |
| Monday 9:05 | Michael and Samir consult a book on money laundering, for research |
| Monday 11:00 | A plan is made to return the money |
| Later that week | The building has a fire. Unrelated. See [facilities](../../teams/facilities/fire-drill.md) |
| Following week | Money returned in full. Change removed |

## What went wrong

1. The change was not reviewed. The reviewer was the author's friend.
2. There was no reconciliation check between the rounding total and the ledger total. See [reconcile.sql](reconcile.sql), added afterwards.
3. The test data had one account, so a fraction of a cent of one account looked like nothing.

## What went right

- The problem was found within one business day.
- Everything was returned.

## Action items

| Action | Owner | State |
|---|---|---|
| Add a daily reconciliation of rounding totals | Michael | Done |
| Require a second reviewer on ledger changes | Samir | Done |
| Use realistic test data, more than one account | Peter | Done |
| Do not get ideas from movies | Everyone | Ongoing |

Sample data: [ledger-sample.csv](ledger-sample.csv).
