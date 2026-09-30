"""Analytic validation of the first-order sensitivity estimators.

Paper 4 replaces the classic Saltelli first-order estimator with a binned
conditional-mean estimator, because M6 (a weighted pass rate) has a standard
deviation of order 1e-2 and the classic estimator returns indices above unity
and negative values at that scale.  This module supplies Table 7 of the
manuscript, in both output regimes:

  panel A  ordinary output scale
             f = x0 + 2*x1      true S1 = 0.200 / 0.800
             f = x0             true S1 = 1.000 / 0.000
           Evaluated without any sd-matching scaling.  Table 7 reports the
           substituted estimator only for this panel, and so does this module.

  panel B  low-variance regime, sd ~ 0.012 (the regime that motivated the
           substitution)
             f = 0.5 + a(x0 + x1)   true S1 = 0.500 / 0.500
             f = 0.5 + b*x0*x1      true S1 = 0.000 / 0.000  (pure interaction)
             f = 0.5 + c*x0         true S1 = 1.000 / 0.000
           Both the classic Saltelli first-order estimator (N = 1024) and the
           binned substitute (N = 4000) are applied, plus the Jansen total-order
           estimator.

Two facts the table has to carry, and previously did not:

1. The binned estimator is **not bin-count invariant**.  For a single-factor
   function its large-N limit is exactly ``1 - 1/B^2``, i.e. 0.993 at B = 12 and
   0.990 at B = 10.  A printed index therefore means nothing without its bin
   count, so ``bins`` is a column of the output rather than a footnote.
   B = 10 is now the value used throughout the paper; see ``DEFAULT_BINS`` in
   ``experiments/sobol.py`` for why ten and not twelve.

2. A single-seed Monte-Carlo figure is a draw, not a stable value.  The
   additive panel-A function has a seed-to-seed spread of about 0.011 on its
   first factor -- wider than the three decimals Table 7 prints.  The output
   therefore carries ``ensemble_mean`` and ``ensemble_sd`` over ``n_seeds``
   independent matrices alongside the single-seed value.

Standard library only.  Deterministic.
"""
from __future__ import annotations

import csv
import math
import os
import random
import sys
from typing import Dict, List

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from experiments.sobol import s1_binned, DEFAULT_BINS  # noqa: E402

RESULTS_DIR = os.path.join(_ROOT, "results")

K = 4
N_BINNED = 4000            # samples for the binned substitute
N_SALTELLI = 1024          # samples for the classic Saltelli estimator
N_JANSEN = 1024            # samples for the Jansen total-order estimator
N_SD_SAMPLE = 40000        # sample used only to report each function's output sd
N_ENSEMBLE = 200           # independent matrices behind ensemble_mean / ensemble_sd
TARGET_SD = 0.012

SD_SEED = 5
BINNED_SEED = 2024
SALTELLI_SEED = 1000 + N_SALTELLI
JANSEN_SEED = 77

# scaling constants chosen so each panel-B function's output sd matches TARGET_SD
A = math.sqrt(TARGET_SD ** 2 * 12 / 2)        # additive, two active factors
B = math.sqrt(TARGET_SD ** 2 / 0.0486111)     # pure interaction x0*x1
C = math.sqrt(TARGET_SD ** 2 * 12)            # single factor

# One bin count for both panels, and it must be the same one Run analyses use.
PANEL_A_BINS = (DEFAULT_BINS,)

PANEL_A_FUNCS = [
    ("additive  f = x0 + 2x1", lambda x: x[0] + 2.0 * x[1],
     [0.2, 0.8, 0.0, 0.0]),
    ("single  f = x0", lambda x: x[0],
     [1.0, 0.0, 0.0, 0.0]),
]

PANEL_B_FUNCS = [
    ("additive  f = 0.5 + a(x0 + x1)", lambda x: 0.5 + A * (x[0] + x[1]),
     [0.5, 0.5, 0.0, 0.0]),
    ("interaction f = 0.5 + b*x0*x1", lambda x: 0.5 + B * x[0] * x[1],
     [0.0, 0.0, 0.0, 0.0]),
    ("single  f = 0.5 + c*x0", lambda x: 0.5 + C * x[0],
     [1.0, 0.0, 0.0, 0.0]),
]

_COLS = [
    "panel", "test_function", "output_sd", "bins", "N",
    "factor_index", "factor_name",
    "true_S1", "saltelli_S1_N1024", "jansen_ST_N1024", "substituted_S1_N4000",
    "ensemble_mean", "ensemble_sd", "n_seeds", "note",
]


def _var(xs) -> float:
    n = len(xs)
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / n


def saltelli_s1(f, n: int, rng) -> List[float]:
    """Classic Saltelli (2010) first-order estimator."""
    A_ = [[rng.random() for _ in range(K)] for _ in range(n)]
    B_ = [[rng.random() for _ in range(K)] for _ in range(n)]
    yA = [f(r) for r in A_]
    yB = [f(r) for r in B_]
    V = _var(yA + yB)
    out = []
    for i in range(K):
        AB = [list(A_[j]) for j in range(n)]
        for j in range(n):
            AB[j][i] = B_[j][i]
        yAB = [f(r) for r in AB]
        out.append(sum(yB[j] * (yAB[j] - yA[j]) for j in range(n)) / n / V)
    return out


def jansen_st(f, n: int, rng) -> List[float]:
    """Jansen/Saltelli total-order estimator."""
    A_ = [[rng.random() for _ in range(K)] for _ in range(n)]
    B_ = [[rng.random() for _ in range(K)] for _ in range(n)]
    yA = [f(r) for r in A_]
    yB = [f(r) for r in B_]
    V = _var(yA + yB)
    out = []
    for i in range(K):
        AB = [list(A_[j]) for j in range(n)]
        for j in range(n):
            AB[j][i] = B_[j][i]
        yAB = [f(r) for r in AB]
        out.append(0.5 * sum((yA[j] - yAB[j]) ** 2 for j in range(n)) / n / V)
    return out


def _output_sd(f) -> float:
    rng = random.Random(SD_SEED)
    return math.sqrt(_var([f([rng.random() for _ in range(K)])
                           for _ in range(N_SD_SAMPLE)]))


def _ensemble(f, bins: int, n_seeds: int = N_ENSEMBLE):
    """Binned first-order indices over independent Monte-Carlo matrices."""
    acc: List[List[float]] = [[] for _ in range(K)]
    for seed in range(n_seeds):
        rng = random.Random(seed)
        MC = [[rng.random() for _ in range(K)] for _ in range(N_BINNED)]
        for i, v in enumerate(s1_binned(MC, [f(r) for r in MC], bins)):
            acc[i].append(v)
    means = [sum(v) / len(v) for v in acc]
    sds = [math.sqrt(_var(v)) for v in acc]
    return means, sds


def _row(panel, name, sd, bins, n, idx, true_s1, salt, jansen, substituted,
         ens_m, ens_sd, n_seeds, note) -> Dict:
    # Six decimals, not four. The estimator columns include values near 1e-3 whose
    # third decimal is decided by the fourth; at four decimals the additive
    # function's inactive factors round across the presentation boundary and a
    # downstream consumer formatting at three decimals sees 0.004 where the
    # estimator returned 0.0035. Six decimals keeps the file unambiguous.
    def f6(v):
        return "" if v is None else round(v, 6)
    return {
        "panel": panel, "test_function": name,
        "output_sd": round(sd, 5), "bins": bins, "N": n,
        "factor_index": idx, "factor_name": f"x{idx}",
        "true_S1": true_s1,
        "saltelli_S1_N1024": f6(salt),
        "jansen_ST_N1024": f6(jansen),
        "substituted_S1_N4000": f6(substituted),
        "ensemble_mean": round(ens_m, 6), "ensemble_sd": round(ens_sd, 6),
        "n_seeds": n_seeds, "note": note,
    }


def run_validation(verbose: bool = True) -> List[Dict]:
    """Write results/estimator_validation.csv and return its rows."""
    rows: List[Dict] = []

    # ---- panel A: ordinary output scale, substituted estimator only -----------
    for bins in PANEL_A_BINS:
        note = f"ordinary output scale; substituted estimator only, as in Table 7 (B = {bins})"
        for name, f, truth in PANEL_A_FUNCS:
            sd = _output_sd(f)
            rng = random.Random(BINNED_SEED)
            MC = [[rng.random() for _ in range(K)] for _ in range(N_BINNED)]
            sub = s1_binned(MC, [f(r) for r in MC], bins)
            ens_m, ens_sd = _ensemble(f, bins)
            for i, t in enumerate(truth):
                rows.append(_row("A", name, sd, bins, N_BINNED, i, t,
                                 None, None, sub[i], ens_m[i], ens_sd[i],
                                 N_ENSEMBLE, note))

    # ---- panel B: low-variance regime, both estimators ------------------------
    note_b = (f"low-variance regime: function scaled so output sd ~ {TARGET_SD}; "
              "Saltelli and Jansen at N = 1024")
    for name, f, truth in PANEL_B_FUNCS:
        sd = _output_sd(f)
        salt = saltelli_s1(f, N_SALTELLI, random.Random(SALTELLI_SEED))
        jansen = jansen_st(f, N_JANSEN, random.Random(JANSEN_SEED))
        rng = random.Random(BINNED_SEED)
        MC = [[rng.random() for _ in range(K)] for _ in range(N_BINNED)]
        sub = s1_binned(MC, [f(r) for r in MC], DEFAULT_BINS)
        ens_m, ens_sd = _ensemble(f, DEFAULT_BINS)
        for i, t in enumerate(truth):
            rows.append(_row("B", name, sd, DEFAULT_BINS, N_BINNED, i, t,
                             salt[i], jansen[i], sub[i], ens_m[i], ens_sd[i],
                             N_ENSEMBLE, note_b))

    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "estimator_validation.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=_COLS)
        w.writeheader()
        w.writerows(rows)

    if verbose:
        def cell(v, width=10, dec=4):
            return f"{v:>{width}.{dec}f}" if v != "" else f"{'-':>{width}}"

        print("\nEstimator validation -- analytic test functions (Table 7)")
        print(f"{'pan':<4}{'bins':>5}  {'test function':<32}{'i':>3}"
              f"{'true':>8}{'Saltelli':>10}{'Jansen':>10}{'subst':>10}"
              f"{'ens mean':>10}{'ens sd':>9}")
        print("-" * 101)
        for r in rows:
            print(f"{r['panel']:<4}{r['bins']:>5}  {r['test_function']:<32}"
                  f"{r['factor_index']:>3}{r['true_S1']:>8.3f}"
                  f"{cell(r['saltelli_S1_N1024'])}"
                  f"{cell(r['jansen_ST_N1024'])}"
                  f"{cell(r['substituted_S1_N4000'])}"
                  f"{r['ensemble_mean']:>10.4f}{r['ensemble_sd']:>9.4f}")
        print(f"\n[written] {path}")
    return rows


if __name__ == "__main__":
    run_validation()
