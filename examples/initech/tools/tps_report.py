#!/usr/bin/env python3
"""Fill in a TPS cover sheet from a unittest run summary.

Usage:
    python3 tps_report.py --project Y2K-INTEREST --tester "Samir Nagheenanajar" results.txt
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import date

MANAGER_BOXES = 8


@dataclass
class CoverSheet:
    project: str
    tester: str
    run: int
    passed: int
    report_date: date = field(default_factory=date.today)
    version: str = "new"

    def render(self) -> str:
        boxes = "  ".join("[    ]" for _ in range(MANAGER_BOXES))
        return "\n".join([
            "TPS REPORT COVER SHEET (new)",
            f"Project code:      {self.project}",
            f"Report date:       {self.report_date.isoformat()}",
            f"Tester:            {self.tester}",
            f"Test cases run:    {self.run}",
            f"Test cases passed: {self.passed}",
            f"Manager initials:  {boxes}",
        ])


def parse_summary(text: str) -> tuple[int, int]:
    """Read 'Ran N tests' and any 'failures=F, errors=E' from unittest output."""
    ran = re.search(r"Ran (\d+) tests?", text)
    if not ran:
        raise ValueError("no 'Ran N tests' line found")
    total = int(ran.group(1))
    bad = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", text))
    return total, total - bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--tester", required=True)
    ap.add_argument("results")
    args = ap.parse_args()
    with open(args.results, encoding="utf-8") as fh:
        run, passed = parse_summary(fh.read())
    print(CoverSheet(args.project, args.tester, run, passed).render())


if __name__ == "__main__":
    main()
