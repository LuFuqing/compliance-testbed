#!/usr/bin/env python3
"""Entry point: run the scenario suite.

  python3 run_all.py

Produces:
  results/scenarios.csv / .json   S0-S6 + B0/B1 baselines
  results/sensitivity.csv         Morris elementary effects on M6
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from experiments.run_scenarios import run_all_scenarios  # noqa: E402
from experiments.sensitivity import run_sensitivity      # noqa: E402


def main():
    print("=" * 72)
    print("Compliance-by-Design Testbed - scenario suite")
    print("=" * 72)
    run_all_scenarios()
    run_sensitivity()
    print("\ndone.")


if __name__ == "__main__":
    main()
