"""Variance-based Sobol sensitivity (pure stdlib).

Hybrid estimator, because the model output has a very small variance (M6 sd ~ 0.015),
which makes the classic Saltelli S1 estimator numerically unusable (its product term
is dominated by noise). We therefore estimate:

  S1  first-order index  -> binned conditional-mean estimator (robust)
        S1_i = Var_bins( E[y | x_i in bin] ) / Var(y)
  ST  total-order index  -> Jansen/Saltelli estimator (stable here)
        ST_i = 0.5 * mean( (f(A) - f(A_B^i))^2 ) / V
  interaction = ST - S1

Validated against analytic functions (additive, pure-interaction, single-factor).
"""
from __future__ import annotations

import csv
import os
import random
import sys
from typing import Dict, List

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.simulator import Params, run  # noqa: E402

RESULTS_DIR = os.path.join(_ROOT, "results")

SPACE = {
    "p_err": (0.0, 0.20),
    "p_skip": (0.0, 0.15),
    "p_atk": (0.0, 0.10),
    "n_stakeholders": (3, 12),
}
NAMES = list(SPACE.keys())
TARGETS = ["M6_conformance_score", "M1_evidence_completeness"]

# Bin count for the binned conditional-mean estimator.
#
# Single source of truth: run_sobol() and s1_binned() both default to it, and
# experiments/estimator_validation.py validates the estimator at this value.
#
# Why 10. The binned estimator is not bin-count invariant -- for a single-factor
# function its large-N limit is exactly 1 - 1/B^2 (0.993 at B = 12, 0.990 at
# B = 10) -- so the count is a reportable parameter, not an implementation
# detail. Ten is chosen because n_stakeholders takes exactly ten integer values
# (3..12 inclusive): at B = 10 every bin maps to one distinct integer, so the
# conditional-mean estimate for that factor is a plain group mean with no
# within-bin mixing. At B = 12 the ten levels fall across twelve bins, some
# bins are empty and one or two hold two levels, which biases that factor's
# index. The three continuous factors are unaffected in kind, only in
# resolution. Changing this value changes every S1 and therefore the published
# numbers, the release fingerprints and the version.
DEFAULT_BINS = 10


def _params(row, timesteps: int) -> Params:
    p = Params(scenario="SOBOL", mode="B2", profile="flood", timesteps=timesteps)
    lo, hi = SPACE["p_err"];          p.p_err = lo + row[0] * (hi - lo)
    lo, hi = SPACE["p_skip"];         p.p_skip = lo + row[1] * (hi - lo)
    lo, hi = SPACE["p_atk"];          p.p_atk = lo + row[2] * (hi - lo)
    lo, hi = SPACE["n_stakeholders"]; p.n_stakeholders = int(round(lo + row[3] * (hi - lo)))
    return p


def _eval_batch(rows, timesteps: int) -> Dict[str, List[float]]:
    acc = {t: [] for t in TARGETS}
    for r in rows:
        m = run(_params(r, timesteps))["metrics"]
        for t in TARGETS:
            v = m[t]
            acc[t].append(float(v) if v is not None else 0.0)
    return acc


def _var(xs):
    n = len(xs)
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / n


def s1_binned(rows, ys, bins: int = DEFAULT_BINS) -> List[float]:
    """First-order index per parameter via binned conditional means."""
    n = len(ys)
    var = _var(ys)
    out = []
    for i in range(len(NAMES)):
        vals = [r[i] for r in rows]
        lo, hi = min(vals), max(vals)
        if hi <= lo:
            out.append(0.0)
            continue
        bk: Dict[int, List[float]] = {}
        for r, y in zip(rows, ys):
            b = min(bins - 1, int((r[i] - lo) / (hi - lo + 1e-12) * bins))
            bk.setdefault(b, []).append(y)
        means = [sum(v) / len(v) for v in bk.values()]
        w = [len(v) / n for v in bk.values()]
        gm = sum(a * b for a, b in zip(w, means))
        vcm = sum(a * (b - gm) ** 2 for a, b in zip(w, means))
        out.append(vcm / var if var > 0 else 0.0)
    return out


SAMPLES_COLS = ["block", "row", "x_p_err", "x_p_skip", "x_p_atk",
                "x_n_stakeholders", "y_M6_conformance_score",
                "y_M1_evidence_completeness"]


def run_sobol(n_base: int = 1024, n_mc: int = 4000, timesteps: int = 30,
              seed: int = 11, bins: int = DEFAULT_BINS, verbose: bool = True,
              write_samples: bool = True):
    rng = random.Random(seed)
    k = len(NAMES)

    # --- first-order indices: large Monte-Carlo + binning ---
    MC = [[rng.random() for _ in range(k)] for _ in range(n_mc)]
    mc = _eval_batch(MC, timesteps)

    # --- total-order indices: Saltelli/Jansen design ---
    A = [[rng.random() for _ in range(k)] for _ in range(n_base)]
    B = [[rng.random() for _ in range(k)] for _ in range(n_base)]
    a = _eval_batch(A, timesteps)
    b = _eval_batch(B, timesteps)
    ab = {}
    ab_rows = {}
    for i in range(k):
        AB = [list(A[j]) for j in range(n_base)]
        for j in range(n_base):
            AB[j][i] = B[j][i]
        ab[i] = _eval_batch(AB, timesteps)
        ab_rows[i] = AB

    rows_out = []
    for t in TARGETS:
        s1 = s1_binned(MC, mc[t], bins)
        yA, yB = a[t], b[t]
        var = _var(yA + yB)
        for i, name in enumerate(NAMES):
            yAB = ab[i][t]
            st = (0.5 * sum((yA[j] - yAB[j]) ** 2 for j in range(n_base)) / n_base / var
                  if var > 0 else 0.0)
            rows_out.append({"target": t, "param": name, "S1": round(s1[i], 4),
                             "ST": round(st, 4), "interaction": round(st - s1[i], 4)})

    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "sobol.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["target", "param", "S1", "ST", "interaction"])
        w.writeheader()
        w.writerows(rows_out)

    samples_path = None
    if write_samples:
        samples_path = _write_samples(MC, A, B, ab, ab_rows, mc, a, b, n_mc, n_base)

    if verbose:
        print(f"\nSobol indices  (S1: binning N={n_mc}, bins={bins} | "
              f"ST: Saltelli N={n_base}, timesteps={timesteps})")
        print(f"{'target':<26}{'param':<16}{'S1':>9}{'ST':>9}{'ST-S1':>9}")
        print("-" * 69)
        for r in rows_out:
            print(f"{r['target']:<26}{r['param']:<16}{r['S1']:>9.4f}"
                  f"{r['ST']:>9.4f}{r['interaction']:>9.4f}")
        for t in TARGETS:
            tot = round(sum(r["S1"] for r in rows_out if r["target"] == t), 4)
            print(f"  sum(S1) [{t}] = {tot}")
        print(f"[written] {path}")
        if samples_path:
            print(f"[written] {samples_path}")
    return rows_out


def _write_samples(MC, A, B, ab, ab_rows, mc, a, b, n_mc: int, n_base: int):
    """Write the sensitivity design's inputs and outputs, in evaluation order.

    This is the "sensitivity input and output samples" item of the manuscript's
    data-availability statement.  The blocks are written in the order the design
    evaluates them, and each block's inputs are the exact matrices the indices
    above were computed from -- nothing is re-drawn, so the file and the indices
    cannot disagree.

      1. MC            the N = n_mc Monte-Carlo matrix behind the binned S1
      2. A, B          the two base matrices of the Saltelli/Jansen design
      3. AB[x_j]       one A matrix with column j replaced by B, per factor

    Both targets are reported for every input row, so a reader can recompute
    either S1 or ST from this file alone.
    """
    path = os.path.join(RESULTS_DIR, "sobol_samples.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SAMPLES_COLS)
        w.writeheader()

        def dump(block: str, rows, out):
            for j, r in enumerate(rows):
                w.writerow({
                    "block": block, "row": j,
                    "x_p_err": f"{r[0]:.12g}", "x_p_skip": f"{r[1]:.12g}",
                    "x_p_atk": f"{r[2]:.12g}", "x_n_stakeholders": f"{r[3]:.12g}",
                    "y_M6_conformance_score": f"{out['M6_conformance_score'][j]:.12g}",
                    "y_M1_evidence_completeness": f"{out['M1_evidence_completeness'][j]:.12g}",
                })

        dump("MC_first_order", MC, mc)
        dump("A_saltelli", A, a)
        dump("B_saltelli", B, b)
        for i, name in enumerate(NAMES):
            dump(f"AB_{name}", ab_rows[i], ab[i])
    return path


if __name__ == "__main__":
    run_sobol()
