"""Figure generation for the scenario and sensitivity results (requires matplotlib).

Produces, into results/figures/:
  fig1_scenarios.png    scenario / baseline comparison (M1, M2, M6)
  fig2_sensitivity.png  Morris mu* + Sobol S1/ST
  fig3_event_phases.png flood-event timeline + per-phase compliance (stress vs nominal)
  fig4_generality.png   flood vs transport profile (RQ-E)

Run with a Python that has matplotlib (e.g. the project venv).
"""
from __future__ import annotations

import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from experiments.flood_event import (DISPATCH_THRESHOLD, PHASES,  # noqa: E402
                                     WARNING_THRESHOLD, rainfall, water_level)

RESULTS = os.path.join(_ROOT, "results")
FIGS = os.path.join(RESULTS, "figures")

C_M1, C_M2, C_M6 = "#2b6cb0", "#dd6b20", "#2f855a"
C_RED, C_BLUE, C_GREY = "#c53030", "#2b6cb0", "#a0aec0"


def _read_csv(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(v):
    return float(v) if v not in ("", None) else float("nan")


# ---------------------------------------------------------------- fig 1
def fig1_scenarios():
    rows = _read_csv("scenarios.csv")
    names = [r["scenario"] for r in rows]
    m1 = [_f(r["M1_evidence_completeness"]) for r in rows]
    m2 = [_f(r["M2_audit_prep_time"]) for r in rows]
    m6 = [_f(r["M6_conformance_score"]) for r in rows]

    fig, ax = plt.subplots(figsize=(11, 4.6))
    x = range(len(names))
    w = 0.38
    ax.bar([i - w / 2 for i in x], m1, w, label="M1 evidence completeness", color=C_M1)
    ax.bar([i + w / 2 for i in x], m6, w, label="M6 conformance score", color=C_M6)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("M1 / M6  (0-1)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=32, ha="right", fontsize=8)
    ax.axvspan(-0.5, 1.5, color=C_GREY, alpha=0.18)
    ax.text(0.5, 1.02, "baselines", ha="center", fontsize=8, color="#4a5568")

    ax2 = ax.twinx()
    ax2.plot(list(x), m2, "o-", color=C_M2, lw=1.8, ms=5, label="M2 audit prep time")
    ax2.set_ylabel("M2 audit preparation time  (lower is better)", color=C_M2)
    ax2.tick_params(axis="y", labelcolor=C_M2)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    # legend placed below the axes in three columns: inside the axes almost every
    # column is occupied from the baseline up, so an in-axes legend overlaps the bars.
    ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.24),
              ncol=3, fontsize=8, framealpha=0.95)
    ax.set_title("Scenario comparison: compliance-by-design vs baselines (flood profile, B2 unless noted)",
                 fontsize=10)
    fig.tight_layout()
    p = os.path.join(FIGS, "fig1_scenarios.png")
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return p


# ---------------------------------------------------------------- fig 2
def fig2_sensitivity():
    mor = _read_csv("sensitivity.csv")
    sob = _read_csv("sobol.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.9))

    # (a) Morris mu*
    ax = axes[0]
    params = [r["param"] for r in mor]
    mustar = [_f(r["mu_star"]) for r in mor]
    ax.bar(params, mustar, color=C_BLUE)
    ax.set_title("(a) Morris $\\mu^*$ on M6", fontsize=9)
    ax.set_ylabel("$\\mu^*$ (elementary-effect magnitude)")
    ax.tick_params(axis="x", rotation=20)

    # (b)(c) Sobol S1/ST per target
    for ax, target, ttl in ((axes[1], "M6_conformance_score", "(b) Sobol on M6"),
                            (axes[2], "M1_evidence_completeness", "(c) Sobol on M1")):
        sub = [r for r in sob if r["target"] == target]
        ps = [r["param"] for r in sub]
        x = range(len(ps))
        w = 0.38
        ax.bar([i - w / 2 for i in x], [_f(r["S1"]) for r in sub], w,
               label="$S_1$ first-order", color=C_M1)
        ax.bar([i + w / 2 for i in x], [_f(r["ST"]) for r in sub], w,
               label="$S_T$ total-order", color=C_M6)
        ax.set_xticks(list(x))
        ax.set_xticklabels(ps, rotation=20, fontsize=8)
        ax.set_ylim(0, 0.7)
        ax.set_title(ttl, fontsize=9)
        ax.set_ylabel("Sobol index")
        ax.legend(fontsize=7)

    fig.suptitle("Sensitivity of compliance to control-quality factors (flood profile)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    p = os.path.join(FIGS, "fig2_sensitivity.png")
    fig.savefig(p, dpi=300)
    plt.close(fig)
    return p


# ---------------------------------------------------------------- fig 3
def fig3_event_phases():
    with open(os.path.join(RESULTS, "calibration.json"), encoding="utf-8") as f:
        cal = json.load(f)
    stressed, nominal = cal["stressed"], cal["nominal"]

    fig, axes = plt.subplots(2, 1, figsize=(11, 6.4), sharex=False,
                             gridspec_kw={"height_ratios": [1.15, 1]})

    # --- (top) event timeline ---
    ax = axes[0]
    ts = [t / 2 for t in range(0, 73)]          # 0..36 h, 0.5 h steps
    rain = [rainfall(t) for t in ts]
    level = [water_level(t) for t in ts]
    for ph in PHASES:
        ax.axvspan(ph.t0, ph.t1, alpha=0.07,
                   color=C_RED if ph.name in ("P3_warning", "P4_dispatch") else C_GREY)
    ax.bar(ts, rain, width=0.5, color=C_M1, alpha=0.55, label="rainfall (mm/h)")
    ax.set_ylabel("rainfall (mm/h)", color=C_M1)
    ax.tick_params(axis="y", labelcolor=C_M1)
    ax2 = ax.twinx()
    ax2.plot(ts, level, color=C_RED, lw=2.0, label="water level (m)")
    ax2.axhline(WARNING_THRESHOLD, ls="--", lw=1.1, color=C_RED, alpha=0.8)
    ax2.axhline(DISPATCH_THRESHOLD, ls=":", lw=1.1, color="#742a2a", alpha=0.9)
    ax2.text(0.4, WARNING_THRESHOLD + 0.05, "warning threshold", fontsize=7, color=C_RED)
    ax2.text(0.4, DISPATCH_THRESHOLD + 0.05, "dispatch threshold", fontsize=7, color="#742a2a")
    ax2.set_ylabel("water level (m)", color=C_RED)
    ax2.tick_params(axis="y", labelcolor=C_RED)
    for ph in PHASES:
        ax2.text((ph.t0 + ph.t1) / 2, 0.965, ph.name.split("_", 1)[1].replace("_", " "),
                 transform=ax2.get_xaxis_transform(),
                 ha="center", va="top", fontsize=7, color="#2d3748",
                 bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, pad=1.4))
    ax.set_title("De-identified urban flood event, aligned to the SL/T 853-855 process "
                 "(data baseplate -> model -> warning -> dispatch)", fontsize=9)
    ax.set_xlabel("hours")

    # --- (bottom) per-phase compliance ---
    ax = axes[1]
    names = [r["phase"].split("_", 1)[1].replace("_", " ") for r in stressed]
    x = range(len(names))
    w = 0.2
    ax.bar([i - 1.5 * w for i in x], [r["M1_evidence_completeness"] for r in stressed], w,
           label="M1 stressed", color=C_M1)
    ax.bar([i - 0.5 * w for i in x], [r["M6_conformance_score"] for r in stressed], w,
           label="M6 stressed", color=C_M6)
    ax.bar([i + 0.5 * w for i in x], [r["M1_evidence_completeness"] for r in nominal], w,
           label="M1 nominal", color=C_M1, alpha=0.45, hatch="//")
    ax.bar([i + 1.5 * w for i in x], [r["M6_conformance_score"] for r in nominal], w,
           label="M6 nominal", color=C_M6, alpha=0.45, hatch="//")
    ax.set_ylim(0.80, 1.02)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, rotation=18, ha="right", fontsize=8)
    ax.set_ylabel("M1 / M6")
    ax.axvspan(2.5, 4.5, color=C_RED, alpha=0.10)
    ax.text(3.5, 1.005, "warning + dispatch", ha="center", fontsize=8, color=C_RED)
    ax.legend(fontsize=7.5, ncol=2, loc="lower left")
    ax.set_title("Compliance degrades exactly at the warning/dispatch peak "
                 "(stressed control quality) - nominal control stays flat", fontsize=9)
    ax.set_xlabel("SL/T 853-855 process phase")

    fig.tight_layout()
    p = os.path.join(FIGS, "fig3_event_phases.png")
    fig.savefig(p, dpi=300)
    plt.close(fig)
    return p


# ---------------------------------------------------------------- fig 4
def fig4_generality():
    rows = _read_csv("scenarios.csv")
    pick = [("S0_full_baseline", "flood baseline"),
            ("S6_transport_baseline", "transport baseline"),
            ("S4_adversarial", "flood adversarial"),
            ("S6b_transport_adv", "transport adversarial")]
    sel = []
    for key, lbl in pick:
        for r in rows:
            if r["scenario"] == key:
                sel.append((lbl, r))
                break

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9))
    labels = [s[0] for s in sel]
    x = range(len(sel))
    w = 0.38

    ax = axes[0]
    ax.bar([i - w / 2 for i in x], [_f(s[1]["M1_evidence_completeness"]) for s in sel], w,
           label="M1 completeness", color=C_M1)
    ax.bar([i + w / 2 for i in x], [_f(s[1]["M6_conformance_score"]) for s in sel], w,
           label="M6 conformance", color=C_M6)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=8)
    ax.set_ylim(0.85, 1.01)
    ax.set_ylabel("M1 / M6")
    ax.legend(fontsize=8)
    ax.set_title("(a) flood vs transport: same trends", fontsize=9)

    ax = axes[1]
    ax.bar([i - w / 2 for i in x], [_f(s[1]["M2_audit_prep_time"]) for s in sel], w,
           label="M2 audit time", color=C_M2)
    ax.bar([i + w / 2 for i in x], [_f(s[1]["M3_violation_detection"]) for s in sel], w,
           label="M3 detection", color="#805ad5")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=8)
    ax.set_ylabel("M2 / M3")
    ax.legend(fontsize=8)
    ax.set_title("(b) detection transfers, cost tracks severity", fontsize=9)

    fig.suptitle("Cross-domain generality (RQ-E): engine + R1-R8 with a profile swap only", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    p = os.path.join(FIGS, "fig4_generality.png")
    fig.savefig(p, dpi=300)
    plt.close(fig)
    return p


def make_all(verbose: bool = True):
    os.makedirs(FIGS, exist_ok=True)
    paths = []
    for fn in (fig1_scenarios, fig2_sensitivity, fig3_event_phases, fig4_generality):
        p = fn()
        paths.append(p)
        if verbose:
            print(f"[figure] {p}")
    return paths


if __name__ == "__main__":
    make_all()
