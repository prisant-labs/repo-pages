"""Expand two-digit years to four digits using a fixed pivot (date windowing).

Used by the Y2K remediation. Years below the pivot are in the 2000s; the rest
are in the 1900s. Revisit before the pivot year arrives.
"""

from __future__ import annotations

from datetime import date

PIVOT = 50


class WindowError(ValueError):
    """A value that cannot be windowed."""


def expand_year(yy: int, pivot: int = PIVOT) -> int:
    """Return the four-digit year for a two-digit year."""
    if not 0 <= yy <= 99:
        raise WindowError(f"not a two-digit year: {yy}")
    if not 0 < pivot < 100:
        raise WindowError(f"pivot must be between 1 and 99: {pivot}")
    return 2000 + yy if yy < pivot else 1900 + yy


def parse_yymmdd(text: str, pivot: int = PIVOT) -> date:
    """Parse a YYMMDD string, as stored by the client systems."""
    if len(text) != 6 or not text.isdigit():
        raise WindowError(f"not a YYMMDD date: {text!r}")
    yy, mm, dd = int(text[:2]), int(text[2:4]), int(text[4:])
    return date(expand_year(yy, pivot), mm, dd)


def days_between(start: str, end: str) -> int:
    """Days from one YYMMDD date to another. Positive when end is later."""
    return (parse_yymmdd(end) - parse_yymmdd(start)).days


if __name__ == "__main__":
    for sample in ("991231", "000101", "490615", "500615"):
        print(sample, "->", parse_yymmdd(sample).isoformat())
