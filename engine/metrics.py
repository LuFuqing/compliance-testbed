"""M1-M6 metrics computed from a batch of handover bundles.

M1 evidence completeness   = fraction of handovers with a valid receipt
M2 audit preparation time  = mean reconstruction cost (lower is better)
M3 violation detection     = detected injected violations / injected
M3s mislabel detection     = detection of the *silent* misclassification channel
M4 handover latency        = mean end-to-end latency
M5 tamper resilience       = fraction of attacked handovers still verifiable
M6 conformance score       = weighted pass rate over R1-R8
"""
from __future__ import annotations

from typing import Dict, List, Optional

from engine.evidence import HandoverBundle
from ruleset import rules as R

# injection tag -> rule(s) that would catch it
DETECT = {
    "mislabel": ("R1", "R2", "R3"),
    "unsigned": ("R4",),
    "no_encrypt": ("R3",),
    "nonlocal": ("R2",),
    "no_audit": ("R5",),
    "pii_unhandled": ("R8",),
    "no_receipt": ("R7",),
    "tamper": ("R6", "R4"),
}


def _conformance(b: HandoverBundle) -> float:
    w = R.WEIGHTS
    tot = sum(w.values())
    lost = sum(w[r] for r in b.detected)
    return (tot - lost) / tot


def m1_completeness(bundles: List[HandoverBundle]) -> float:
    return sum(1 for b in bundles if b.verified) / len(bundles)


def m2_audit_time(bundles: List[HandoverBundle]) -> float:
    total = 0.0
    for b in bundles:
        c = 0.05                                   # baseline reconstruction
        if not b.ev2.signed:
            c += 1.0                               # manual signature check
        if b.ev5.tampered:
            c += 2.0                               # forensic reconstruction
        if not b.ev5.well_formed:
            c += 1.5                               # rebuild missing receipt
        c += 0.5 * len(b.detected)                 # per-violation handling
        total += c
    return total / len(bundles)


def _detection_counts(bundles):
    inj = det = inj_mis = det_mis = 0
    for b in bundles:
        fail = set(b.detected)
        for tag in b.injected:
            inj += 1
            hit = any(r in fail for r in DETECT.get(tag, ()))
            if hit:
                det += 1
            if tag == "mislabel":
                inj_mis += 1
                if hit:
                    det_mis += 1
    return inj, det, inj_mis, det_mis


def m3_detection(bundles) -> float:
    inj, det, _, _ = _detection_counts(bundles)
    return det / inj if inj else 1.0


def m3s_mislabel_detection(bundles) -> Optional[float]:
    _, _, inj_mis, det_mis = _detection_counts(bundles)
    return (det_mis / inj_mis) if inj_mis else None


def m4_latency(bundles) -> float:
    return sum(b.latency for b in bundles) / len(bundles)


def m5_tamper_resilience(bundles) -> Optional[float]:
    """Fraction of attacked handovers whose evidence survives (is recovered)."""
    attacked = [b for b in bundles if b.ev5.tampered]
    if not attacked:
        return None
    return sum(1 for b in attacked if b.recovered) / len(attacked)


def m6_conformance(bundles) -> float:
    return sum(_conformance(b) for b in bundles) / len(bundles)


def compute(bundles: List[HandoverBundle], params=None) -> Dict[str, object]:
    return {
        "n_handovers": len(bundles),
        "M1_evidence_completeness": round(m1_completeness(bundles), 4),
        "M2_audit_prep_time": round(m2_audit_time(bundles), 4),
        "M3_violation_detection": round(m3_detection(bundles), 4),
        "M3s_mislabel_detection": (None if m3s_mislabel_detection(bundles) is None
                                   else round(m3s_mislabel_detection(bundles), 4)),
        "M4_handover_latency": round(m4_latency(bundles), 4),
        "M5_tamper_resilience": (None if m5_tamper_resilience(bundles) is None
                                 else round(m5_tamper_resilience(bundles), 4)),
        "M6_conformance_score": round(m6_conformance(bundles), 4),
    }


# ---------------------------------------------------------------- supplementary
# The helpers below are additive: they expose the raw detection counts behind M3/M3s
# and a Wilson interval for them, so the released supplementary tables can report the
# sample sizes that the rates rest on. They do NOT alter compute() or any metric value,
# so the four release fingerprints are unaffected.

def detection_counts(bundles) -> Dict[str, int]:
    """Raw injection/detection counts behind M3 and M3s.

    ``n_mislabels_*`` counts only the silent-misclassification channel (tag
    ``mislabel``), which is what M3s reports; ``n_injected``/``n_detected`` cover
    every injected tag, which is what M3 reports.
    """
    inj, det, inj_mis, det_mis = _detection_counts(bundles)
    return {
        "n_injected": inj,
        "n_detected": det,
        "n_injected_undetected": inj - det,
        "n_mislabels_injected": inj_mis,
        "n_mislabels_detected": det_mis,
        "n_mislabels_undetected": inj_mis - det_mis,
    }


def wilson_interval(k: int, n: int, z: float = 1.959963984540054):
    """Two-sided Wilson score interval for k successes in n trials.

    Returns ``(low, high)`` rounded to 4 decimals, or ``(None, None)`` when n == 0.
    The Wilson interval is used rather than the normal approximation because the
    per-phase mislabel counts are small (single digits), where the normal
    approximation is not admissible.
    """
    if n <= 0:
        return (None, None)
    p = k / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)) / d
    return (round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4))
