"""Domain-profile interface.

A profile is the *only* thing that changes between domains.  It maps a city
subsystem onto the generic metamodel (physical -> data -> virtual -> service)
and tells the engine which data items exist, how they are classified, which
carry PII, which model components form the SBOM, and which organisations
exchange evidence.  The engine and the R1-R8 rule set are profile-independent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SourceSpec:
    """A physical sensing/actuation entity emitting a class of data items."""
    source_id: str
    domain: str
    data_class: str           # "general" | "important" | "core"
    pii: bool = False


@dataclass
class Profile:
    name: str
    domain: str
    standard_anchors: List[str]
    sources: List[SourceSpec]
    models: List[str]
    agencies: List[str]
    org_nodes: int = 5        # number of organisations in the handover graph

    def data_mix(self) -> dict:
        mix = {"general": 0, "important": 0, "core": 0, "pii": 0}
        for s in self.sources:
            mix[s.data_class] = mix.get(s.data_class, 0) + 1
            if s.pii:
                mix["pii"] += 1
        return mix
