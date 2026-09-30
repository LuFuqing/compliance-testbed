"""Scenario runner: S0-S6 (plus B0/B1 baselines).

Writes results/scenarios.csv and results/scenarios.json and prints a table.

Scenario map (see design doc):
  B0_none                baseline: no compliance-by-design          flood
  B1_partial             baseline: labels+encryption+audit only      flood
  S0_full_baseline       full R1-R8, nominal parameters              flood
  S1_mislabel_high       p_err up                                    flood
  S2_unsigned_high       p_skip up                                   flood
  S3_mesh_topology       mesh instead of star                        flood
  S4_adversarial         p_atk up                                    flood
  S5_scale_N12           N = 12 stakeholders                         flood
  S6_transport_baseline  profile swap -> transport (RQ-E)            transport
  S6b_transport_adv      profile swap + adversarial                  transport
"""
from __future__ import annotations

import csv
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from engine.simulator import Params, run  # noqa: E402

RESULTS_DIR = os.path.join(_ROOT, "results")

SCENARIOS = [
    Params(scenario="B0_none", mode="B0", profile="flood"),
    Params(scenario="B1_partial", mode="B1", profile="flood"),
    Params(scenario="S0_full_baseline", mode="B2", profile="flood"),
    Params(scenario="S1_mislabel_high", mode="B2", profile="flood", p_err=0.15),
    Params(scenario="S2_unsigned_high", mode="B2", profile="flood", p_skip=0.10),
    Params(scenario="S3_mesh_topology", mode="B2", profile="flood", topology="mesh"),
    Params(scenario="S4_adversarial", mode="B2", profile="flood", p_atk=0.08),
    Params(scenario="S5_scale_N12", mode="B2", profile="flood", n_stakeholders=12),
    Params(scenario="S6_transport_baseline", mode="B2", profile="transport"),
    Params(scenario="S6b_transport_adv", mode="B2", profile="transport", p_atk=0.08),
]

COLS = ["scenario", "mode", "profile", "p_err", "p_skip", "p_atk", "topology",
        "n_stakeholders", "n_handovers",
        "M1_evidence_completeness", "M2_audit_prep_time", "M3_violation_detection",
        "M3s_mislabel_detection", "M4_handover_latency", "M5_tamper_resilience",
        "M6_conformance_score"]


def _row(res) -> dict:
    p = res["params"]
    m = dict(res["metrics"])
    return {
        "scenario": p.scenario, "mode": p.mode, "profile": p.profile,
        "p_err": p.p_err, "p_skip": p.p_skip, "p_atk": p.p_atk,
        "topology": p.topology, "n_stakeholders": p.n_stakeholders,
        "n_handovers": m["n_handovers"],
        "M1_evidence_completeness": m["M1_evidence_completeness"],
        "M2_audit_prep_time": m["M2_audit_prep_time"],
        "M3_violation_detection": m["M3_violation_detection"],
        "M3s_mislabel_detection": m["M3s_mislabel_detection"],
        "M4_handover_latency": m["M4_handover_latency"],
        "M5_tamper_resilience": m["M5_tamper_resilience"],
        "M6_conformance_score": m["M6_conformance_score"],
    }


def run_all_scenarios(verbose: bool = True, sink: list = None):
    """Run the scenario suite and write scenarios.csv/.json.

    ``sink`` is an optional list that additionally receives ``(row, bundles)``
    pairs; it exists for ``experiments/supplementary.py``, which reports the
    injection/detection counts behind M3/M3s.  Supplying a sink cannot change
    the two output files.
    """
    rows = []
    for sc in SCENARIOS:
        res = run(sc)
        row = _row(res)
        rows.append(row)
        if sink is not None:
            sink.append((row, res["bundles"]))

    os.makedirs(RESULTS_DIR, exist_ok=True)
    csv_path = os.path.join(RESULTS_DIR, "scenarios.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r[k] is None else r[k]) for k in COLS})

    json_path = os.path.join(RESULTS_DIR, "scenarios.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    if verbose:
        _print_table(rows)
        print(f"\n[written] {csv_path}")
        print(f"[written] {json_path}")
    return rows


def _fmt(v):
    return "-" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))


def _print_table(rows):
    head = ["scenario", "prof", "M1", "M2", "M3", "M3s", "M4", "M5", "M6"]
    widths = [22, 9, 6, 6, 6, 6, 6, 6, 6]
    line = "  ".join(h.ljust(w) for h, w in zip(head, widths))
    print("\n" + line)
    print("-" * len(line))
    for r in rows:
        cells = [r["scenario"], r["profile"], _fmt(r["M1_evidence_completeness"]),
                 _fmt(r["M2_audit_prep_time"]), _fmt(r["M3_violation_detection"]),
                 _fmt(r["M3s_mislabel_detection"]), _fmt(r["M4_handover_latency"]),
                 _fmt(r["M5_tamper_resilience"]), _fmt(r["M6_conformance_score"])]
        print("  ".join(c.ljust(w) for c, w in zip(cells, widths)))


if __name__ == "__main__":
    run_all_scenarios()
