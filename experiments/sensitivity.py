"""Morris elementary-effects screening.

Screens the four continuous/discrete parameters against a target metric
(default M6 conformance score) to rank which factors drive compliance loss.
Pure stdlib - no SALib dependency.
"""
from __future__ import annotations

import csv
import os
import random
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.simulator import Params, run  # noqa: E402

RESULTS_DIR = os.path.join(_ROOT, "results")

# normalised space: param -> (min, max)
SPACE = {
    "p_err": (0.0, 0.20),
    "p_skip": (0.0, 0.15),
    "p_atk": (0.0, 0.10),
    "n_stakeholders": (3, 12),
}
TARGET = "M6_conformance_score"


def _params_from_x(x: dict) -> Params:
    p = Params(scenario="MORRIS", mode="B2", profile="flood")
    lo, hi = SPACE["p_err"];          p.p_err = lo + x["p_err"] * (hi - lo)
    lo, hi = SPACE["p_skip"];         p.p_skip = lo + x["p_skip"] * (hi - lo)
    lo, hi = SPACE["p_atk"];          p.p_atk = lo + x["p_atk"] * (hi - lo)
    lo, hi = SPACE["n_stakeholders"]; p.n_stakeholders = int(round(lo + x["n_stakeholders"] * (hi - lo)))
    return p


def _y(x: dict, target: str = TARGET) -> float:
    return run(_params_from_x(x))["metrics"][target]


def morris(r: int = 12, levels: int = 4, seed: int = 7, target: str = TARGET):
    rng = random.Random(seed)
    names = list(SPACE.keys())
    delta = levels / (2.0 * (levels - 1))
    grid = [i / (levels - 1) for i in range(levels)]
    starts = [g for g in grid if g + delta <= 1.0 + 1e-9]

    ee = {n: [] for n in names}
    for _ in range(r):
        x = {n: rng.choice(starts) for n in names}
        y_prev = _y(x, target)
        order = names[:]
        rng.shuffle(order)
        for n in order:
            x[n] = x[n] + delta
            y_new = _y(x, target)
            ee[n].append((y_new - y_prev) / delta)
            y_prev = y_new

    out = []
    for n in names:
        vals = ee[n]
        mu = sum(vals) / len(vals)
        mu_star = sum(abs(v) for v in vals) / len(vals)
        var = sum((v - mu) ** 2 for v in vals) / len(vals)
        out.append({"param": n, "mu": round(mu, 6), "mu_star": round(mu_star, 6),
                    "sigma": round(var ** 0.5, 6)})
    out.sort(key=lambda d: -d["mu_star"])
    return out


def run_sensitivity(verbose: bool = True, target: str = TARGET):
    rows = morris(target=target)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "sensitivity.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["param", "mu", "mu_star", "sigma"])
        w.writeheader()
        w.writerows(rows)
    if verbose:
        print(f"\nMorris elementary effects on {target}  (r=12, levels=4)")
        print(f"{'param':<16}{'mu':>10}{'mu*':>10}{'sigma':>10}")
        print("-" * 46)
        for r_ in rows:
            print(f"{r_['param']:<16}{r_['mu']:>10.4f}{r_['mu_star']:>10.4f}{r_['sigma']:>10.4f}")
        print(f"[written] {path}")
    return rows


if __name__ == "__main__":
    run_sensitivity()
