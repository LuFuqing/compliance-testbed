"""Discrete-event simulation engine (domain-agnostic).

Wires the domain profile, the R1-R8 rule set and the agents together and runs a
batch of cross-organisational handovers, returning M1-M6.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import random
from typing import Dict

from engine import agents as A
from engine import metrics as M
from ruleset import rules as R
from profiles import flood as P_flood, transport as P_transport

PROFILES = {"flood": P_flood, "transport": P_transport}


@dataclass
class Params:
    scenario: str = "S0"
    mode: str = "B2"                 # B0 | B1 | B2
    profile: str = "flood"           # flood | transport
    p_err: float = 0.02              # misclassification probability
    p_skip: float = 0.01             # signature-skip probability
    p_atk: float = 0.01              # adversary probability
    p_noaudit: float = 0.02          # audit-log omission probability
    p_pii_fail: float = 0.02         # PII-handling failure probability
    topology: str = "star"           # star | mesh
    n_stakeholders: int = 5
    timesteps: int = 200
    seed: int = 42

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _latency(params: Params, rng: random.Random) -> float:
    base = 1.0
    topo = {"star": 1.25, "mesh": 0.85}.get(params.topology, 1.0)
    scale = 1.0 + 0.03 * max(0, params.n_stakeholders - 5)
    return round(base * topo * scale * rng.uniform(0.9, 1.1), 4)


def run(params: Params) -> Dict[str, object]:
    rng = random.Random(params.seed)
    profile = PROFILES[params.profile].build()

    sources = [A.Source(s, rng) for s in profile.sources]
    operator = A.Operator(profile, params, rng)
    attacker = A.Attacker(params, rng)
    agency = A.Agency()
    auditor = A.Auditor(R)

    bundles = []
    for t in range(1, params.timesteps + 1):
        for src in sources:
            item = src.emit(t)
            b = operator.process(item, t)
            b.latency = _latency(params, rng)
            if rng.random() < params.p_atk:
                attacker.tamper(b)
            b.verified = agency.verify(b)
            auditor.evaluate(b)
            bundles.append(b)

    return {
        "params": params,
        "profile": profile,
        "metrics": M.compute(bundles, params),
        "bundles": bundles,
    }
