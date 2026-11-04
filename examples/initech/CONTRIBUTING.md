---
description: How to add or change a page on the Initech intranet, including the mandatory cover sheet for wiki edits.
tags: [initech, process, wiki]
---

# Contributing to the intranet

Thank you for improving the intranet. Management appreciates your initiative and would like you to route it through the proper channels.

## Before you edit

1. Fill in a [TPS cover sheet](forms/tps-cover-sheet.pdf). Yes, for wiki edits too. The memo went out.
2. Get sign-off from your manager. If you have eight managers, get sign-off from all eight.
3. Check the [archive](_archive/) to make sure someone has not already written your page in 1998.

## Writing a page

- Start with front matter:

```yaml
---
description: One sentence that says what the page is for.
tags: [team, topic]
---
```

- Use one `#` heading at the top and `##` for sections. The outline on the right is built from them.
- Prefer tables to long lists when you are comparing things.
- Put data in `data/` as CSV, not as a table pasted into a memo.

## File names

Lowercase with dashes: `saturday-coverage.md`, not `Saturday Coverage FINAL (2).md`. There is one exception in `memos/from-bill-lumbergh/`, kept as a warning.

## Review

Open a pull request. Michael or Samir will review it when the printer is working.
