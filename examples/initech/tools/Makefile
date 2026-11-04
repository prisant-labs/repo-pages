PYTHON ?= python3

.PHONY: tps test

# Fill a cover sheet from the latest test run.
tps:
	$(PYTHON) -m unittest discover -s ../projects/y2k-remediation 2> results.txt || true
	$(PYTHON) tps_report.py --project Y2K-INTEREST --tester "$$USER" results.txt

test:
	$(PYTHON) -m unittest discover -s ../projects/y2k-remediation
