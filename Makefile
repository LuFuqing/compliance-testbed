# Compliance-by-Design Simulation Testbed
#
#   make            scenario suite + stress/sensitivity + supplementary + manifest + verification
#   make reproduce  one-click reproduction via reproduce.sh
#   make verify     golden-value verification only
#   make manifest   write results/SHA256SUMS (the archive manifest)
#   make release    build dist/*.zip and dist/*.tar.gz
#
# Order matters: `make release` refuses to package a tree whose results/SHA256SUMS
# is stale, so run `make` (or ./reproduce.sh) first. Override with
# `python3 make_release.py --force` if you deliberately want a stale manifest.
#
# Override the interpreter with:  make PYTHON=/path/to/python

PYTHON  ?= python3
VERSION := $(shell cat VERSION 2>/dev/null || echo unknown)
NAME    := compliance_testbed-$(VERSION)

.PHONY: help all reproduce scenario stress verify strict fingerprints manifest manifest-check clean release licenses distclean

help:
	@awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' $(firstword $(MAKEFILE_LIST))

# The manifest must be written before verify, which checks it.
all: scenario stress manifest verify

reproduce:
	./reproduce.sh

scenario:
	$(PYTHON) run_all.py

stress:
	$(PYTHON) run_stress_sensitivity.py

verify:
	$(PYTHON) verify_results.py

strict:
	$(PYTHON) verify_results.py --strict

# MD5 fingerprints of the four generated CSVs (drift report).
fingerprints:
	$(PYTHON) verify_results.py --manifest

# SHA-256 manifest of the whole artifact (results/SHA256SUMS).
manifest:
	$(PYTHON) make_manifest.py

manifest-check:
	$(PYTHON) make_manifest.py --check

# Remove only the generated results - the code and release metadata stay.
clean:
	rm -rf results
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

# Remove build leftovers and archives as well.
distclean: clean
	rm -rf dist build .venv

# Build the release archives. make_release.py itself checks the manifest first and
# exits non-zero on drift, so this target needs no separate dependency.
release:
	$(PYTHON) make_release.py

# Refresh the vendored CC BY 4.0 legal text from the canonical source.
licenses:
	curl -sSL -o LICENSE-DATA https://creativecommons.org/licenses/by/4.0/legalcode.txt
	@echo "LICENSE-DATA refreshed from creativecommons.org"
