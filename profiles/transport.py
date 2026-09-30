"""Urban transport profile - the cross-domain generalisation probe.

Used in scenario S6 to test RQ-E: does the *same* engine + R1-R8 rule set, with
only a profile swap, hold across a different city subsystem?  Only a light
instantiation is required - the aim is trend consistency, not equal magnitudes.

Architecture anchor: GB/T 45109.1-2024 (shared metamodel).
Domain anchors: GB/T 22239-2019, GB/T 43697-2024, GB/T 39786-2021, PIPL
(the domain-agnostic regulatory stack; no transport-specific DT security
standard is assumed to exist).
"""
from __future__ import annotations

from profiles.base import Profile, SourceSpec


def build() -> Profile:
    sources = [
        SourceSpec("loop_detector", "traffic flow", "general"),
        SourceSpec("signal_controller", "signal control", "core"),
        SourceSpec("gps_probe", "vehicle trajectory", "important", pii=True),
        SourceSpec("cctv_junction", "video surveillance", "important", pii=True),
        SourceSpec("weather_station", "road weather", "general"),
        SourceSpec("transit_afc", "transit ridership", "important", pii=True),
    ]
    return Profile(
        name="transport",
        domain="urban transport / mobility",
        standard_anchors=[
            "GB/T 45109.1-2024",
            "GB/T 43697-2024",
            "GB/T 39786-2021",
            "GB/T 22239-2019",
            "20262810-T-907 (draft, plan number)",
            "PIPL / compliance-audit measures",
        ],
        sources=sources,
        models=["traffic_flow_model", "signal_optimisation_model", "eta_predictor"],
        agencies=["transport_commission", "traffic_police",
                  "transit_operator", "cloud_provider", "regulator_auditor"],
        org_nodes=5,
    )
