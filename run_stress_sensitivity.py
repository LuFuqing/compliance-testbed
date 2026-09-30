#!/usr/bin/env python3
"""Entry point: SL/T 853-855 process stress contrast + Sobol sensitivity
+ supplementary tables + figures.

  python3 run_stress_sensitivity.py                # contrast + Sobol + supplementary + figures
  python3 run_stress_sensitivity.py --no-figures   # ... without figures

The contrast and Sobol stages are pure standard library and always run.  Only
figure generation needs matplotlib, so it degrades gracefully: if matplotlib is
unavailable the figures are skipped with a notice and ``--no-figures`` is
implied.

Naming note: the flood experiment is a **stress contrast**, not a calibration.
The load schedule and the control-stress profile are both assigned by the
analyst in one table; nothing here is fitted to observed data.  The module and
output file names (``experiments/calibration.py``, ``results/calibration.csv``)
are retained for stability, but no output calls the experiment a calibration.

Naming note: this stage was previously called ``T10``.  It is now named for what it
runs -- the process stress contrast and the sensitivity analysis -- and the entry point
is ``run_stress_sensitivity.py``.  Nothing about the computation changed.

This stage also writes the three supplementary tables promised by the
manuscript's data-availability statement.  It runs last because the stress
contrast spans both experiment families.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from experiments.calibration import run_calibration               # noqa: E402
from experiments.sobol import run_sobol                           # noqa: E402
from experiments.supplementary import run_stress_contrast         # noqa: E402
from experiments.estimator_validation import run_validation       # noqa: E402


def main() -> int:
    want_figures = "--no-figures" not in sys.argv

    print("=" * 72)
    print("Stress and sensitivity - SL/T 853-855 process stress contrast + Sobol sensitivity")
    print("=" * 72)

    run_calibration()
    run_sobol()

    print("\n" + "=" * 72)
    print("Supplementary tables (data-availability statement)")
    print("=" * 72)
    run_stress_contrast()
    run_validation()

    if not want_figures:
        print("[skip figures] disabled by --no-figures")
    else:
        try:
            from experiments.figures import make_all
        except ImportError as exc:                   # matplotlib absent
            print(f"[skip figures] matplotlib unavailable: {exc}")
            print("               install it for a full reproduction, e.g.")
            print("               python3 -m pip install matplotlib")
        else:
            make_all()

    print("\ndone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
