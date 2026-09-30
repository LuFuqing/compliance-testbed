"""Semi-synthetic urban flood event, mapped onto the SL/T 853-855 process.

SL/T 853-855-2025 defines the digital-twin water process as
    data baseplate -> model -> early warning -> dispatch  (数据底板 -> 模型 -> 预警 -> 调度)

This module encodes a de-identified 36-hour urban flood event as six phases. Each
phase carries (a) an *evidence load* (relative rate of cross-organisational
handovers) and (b) a *control stress* profile - under time pressure, operators
misclassify more, skip signatures more often and attackers get more chances.
That stress coupling is the object of the stress contrast: does compliance
hold exactly when the event is most severe?

Both the load and the stress profile are analyst-assigned, so the contrast
measures the model's behaviour under an assumed coupling; it is not a
calibration to observed data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Phase:
    name: str
    stage: str              # SL/T 853-855 process stage
    t0: float               # hours
    t1: float
    load: float             # relative handover rate
    stress: Dict[str, float]  # p_err / p_skip / p_atk under this phase


# 6 phases over 36 h
PHASES: List[Phase] = [
    Phase("P0_pre_event", "monitoring baseline", 0, 6, 1.0,
          {"p_err": 0.010, "p_skip": 0.005, "p_atk": 0.002}),
    Phase("P1_data_baseplate", "data baseplate (数据底板)", 6, 12, 1.6,
          {"p_err": 0.020, "p_skip": 0.010, "p_atk": 0.005}),
    Phase("P2_model_inference", "model inference (模型)", 12, 18, 2.2,
          {"p_err": 0.030, "p_skip": 0.015, "p_atk": 0.010}),
    Phase("P3_warning", "early warning (预警)", 18, 21, 3.0,
          {"p_err": 0.060, "p_skip": 0.040, "p_atk": 0.020}),
    Phase("P4_dispatch", "dispatch (调度)", 21, 27, 3.2,
          {"p_err": 0.080, "p_skip": 0.060, "p_atk": 0.030}),
    Phase("P5_recession", "recession / post-event review (复盘)", 27, 36, 1.2,
          {"p_err": 0.020, "p_skip": 0.010, "p_atk": 0.005}),
]

# nominal (fair-weather) control quality, used as the un-stressed contrast
NOMINAL_STRESS = {"p_err": 0.010, "p_skip": 0.005, "p_atk": 0.002}

BASE_PHASE_HANDOVERS = 120


def rainfall(t: float) -> float:
    """De-identified urban rainfall hyetograph (mm/h), peaking at t = 18 h."""
    if t < 7 or t > 33:
        return 0.0
    peak, sigma = 18.0, 5.5
    return round(48.0 * pow(2.718281828, -((t - peak) ** 2) / (2 * sigma ** 2)), 2)


def water_level(t: float) -> float:
    """Catchment water level (m) lagging the rainfall.

    Calibrated (k = 0.01431, base = 2.2 m) so that the hydrograph is *in phase* with
    the SL/T 853-855 operational stages rather than with the raw rainfall:

        peak level        5.600 m at t = 22 h   -> inside the dispatch phase (21-27 h)
        warning 4.5 m     exceeded 16-27 h      -> covers the warning phase (18-21 h)
        dispatch 5.2 m    exceeded 19-25 h      -> covers the dispatch phase (21-27 h)

    The 2 h lead of the 4.5 m crossing (16 h) over the declared warning stage (18 h)
    is the intended lag: a stage is *declared* once the level has held above the
    threshold, so the physical crossing necessarily precedes the designation.
    """
    base, k = 2.2, 0.01431
    resp = 0.0
    for tt in range(0, int(t) + 1):
        r = rainfall(float(tt))
        if r:
            resp += r * pow(2.718281828, -(t - tt) / 6.0)
    return round(base + k * resp, 3)


WARNING_THRESHOLD = 4.5
DISPATCH_THRESHOLD = 5.2


def phase_of(t: float) -> str:
    for p in PHASES:
        if p.t0 <= t < p.t1:
            return p.name
    return PHASES[-1].name
