"""Process stress contrast against the SL/T 853-855 process.

Runs the engine phase-by-phase over the de-identified flood event and contrasts
two regimes:
  stressed  - control quality degrades with event severity (assumed coupling)
  nominal   - control quality held at fair-weather level throughout

The question: does compliance hold when it matters most?

Naming: this is a **scenario contrast under an assumed coupling, not a
calibration to observed data**.  The load schedule and the stress profile are
both assigned by the analyst in one table (experiments/flood_event.py), and
nothing here is fitted to measurements.  The module name and the output file
names are retained for stability.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from typing import Dict, List

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.simulator import Params, run, PROFILES          # noqa: E402
from experiments.flood_event import (BASE_PHASE_HANDOVERS,  # noqa: E402
                                     NOMINAL_STRESS, PHASES)

RESULTS_DIR = os.path.join(_ROOT, "results")

METRIC_KEYS = ["M1_evidence_completeness", "M2_audit_prep_time",
               "M3_violation_detection", "M3s_mislabel_detection",
               "M4_handover_latency", "M5_tamper_resilience",
               "M6_conformance_score"]


def run_event(mode: str = "B2", profile: str = "flood", seed: int = 42,
              stressed: bool = True, base: int = BASE_PHASE_HANDOVERS,
              sink: List = None) -> List[dict]:
    """Per-phase rows for one control-quality regime.

    ``sink`` is an optional list that additionally receives ``(row, bundles)``
    pairs.  It exists for ``experiments/supplementary.py``, which needs the raw
    handover bundles to report injection/detection counts; the row dicts are
    unaffected, so ``run_calibration`` and the two calibrated output files are
    byte-identical whether or not a sink is supplied.
    """
    n_src = len(PROFILES[profile].build().sources)
    rows = []
    for i, ph in enumerate(PHASES):
        n = int(round(base * ph.load))
        ts = max(1, n // n_src)
        p = Params(scenario=ph.name, mode=mode, profile=profile,
                   timesteps=ts, seed=seed + 17 * i)
        s = ph.stress if stressed else NOMINAL_STRESS
        p.p_err, p.p_skip, p.p_atk = s["p_err"], s["p_skip"], s["p_atk"]
        res = run(p)
        m = res["metrics"]
        row = {"phase": ph.name, "stage": ph.stage, "t0": ph.t0, "t1": ph.t1,
               "load": ph.load, "hours": ph.t1 - ph.t0,
               "p_err": p.p_err, "p_skip": p.p_skip, "p_atk": p.p_atk,
               "n_handovers": m["n_handovers"]}
        for k in METRIC_KEYS:
            row[k] = m[k]
        rows.append(row)
        if sink is not None:
            sink.append((row, res["bundles"]))
    return rows


def _pearson(xs, ys) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def run_calibration(verbose: bool = True):
    stressed = run_event(stressed=True)
    nominal = run_event(stressed=False)

    # alignment: does compliance loss track event load?
    loads = [r["load"] for r in stressed]
    losses = [1.0 - r["M6_conformance_score"] for r in stressed]
    m2s = [r["M2_audit_prep_time"] for r in stressed]
    corr_m6 = round(_pearson(loads, losses), 4)
    corr_m2 = round(_pearson(loads, m2s), 4)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "calibration.csv"), "w", newline="",
              encoding="utf-8") as f:
        cols = (["phase", "stage", "t0", "t1", "hours", "load",
                 "p_err", "p_skip", "p_atk", "n_handovers"] + METRIC_KEYS)
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in stressed:
            w.writerow({k: ("" if r.get(k) is None else r[k]) for k in cols})

    summary = {"stressed": stressed, "nominal": nominal,
               "corr_load_vs_M6loss": corr_m6, "corr_load_vs_M2": corr_m2}
    with open(os.path.join(RESULTS_DIR, "calibration.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    if verbose:
        _print(stressed, nominal, corr_m6, corr_m2)
    return summary


def _print(stressed, nominal, corr_m6, corr_m2):
    print("\nT10 - SL/T 853-855 process stress contrast (flood profile, B2)")
    print(f"{'phase':<20}{'load':>6}{'M1':>8}{'M2':>8}{'M6':>8}"
          f"{'M1*':>8}{'M6*':>8}")
    print("-" * 66)
    for s, n in zip(stressed, nominal):
        print(f"{s['phase']:<20}{s['load']:>6.1f}"
              f"{s['M1_evidence_completeness']:>8.3f}{s['M2_audit_prep_time']:>8.3f}"
              f"{s['M6_conformance_score']:>8.3f}"
              f"{n['M1_evidence_completeness']:>8.3f}{n['M6_conformance_score']:>8.3f}")
    print("(* = nominal control quality; M1 completeness, M2 audit time, M6 conformance)")
    print(f"\ncorr(event load, M6 loss)  = {corr_m6:+.4f}")
    print(f"corr(event load, M2 cost)  = {corr_m2:+.4f}")


if __name__ == "__main__":
    run_calibration()
