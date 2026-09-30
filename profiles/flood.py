"""Flood / water digital-twin profile - the primary validation case.

Domain standard: SL/T 853-855-2025 (数字孪生流域 / 水网 / 水利工程建设技术导则).
Architecture anchor: GB/T 45109.1-2024 (city digital twin, technical reference architecture).

Physical layer   rain gauges, water-level stations, gates, pumping stations, CCTV
Data layer       real-time telemetry, data baseplate (SL/T 853 "数据底板"), model inputs
Virtual layer    hydrodynamic + pipe-network coupled flood-evolution model
Service layer    early warning, emergency dispatch, cross-agency sharing
Handover seam    water bureau <-> emergency / urban management <-> cloud provider
"""
from __future__ import annotations

from profiles.base import Profile, SourceSpec


def build() -> Profile:
    sources = [
        SourceSpec("rain_gauge", "precipitation", "general"),
        SourceSpec("water_level", "hydrology", "important"),
        SourceSpec("gate_control", "hydraulic control", "core"),
        SourceSpec("pump_station", "drainage", "important"),
        SourceSpec("cctv_river", "video surveillance", "important", pii=True),
        SourceSpec("population_grid", "affected population", "core", pii=True),
    ]
    return Profile(
        name="flood",
        domain="urban flood / water",
        standard_anchors=[
            "GB/T 45109.1-2024",
            "SL/T 853-2025",
            "SL/T 854-2025",
            "SL/T 855-2025",
            "GB/T 43697-2024",
            "GB/T 39786-2021",
            "GB/T 22239-2019",
            "20262810-T-907 (draft, plan number)",
            "PIPL / compliance-audit measures",
        ],
        sources=sources,
        models=["hydrodynamic_flood_model", "pipe_network_model", "forecast_engine"],
        agencies=["water_bureau", "emergency_management", "urban_management",
                  "cloud_provider", "regulator_auditor"],
        org_nodes=5,
    )
