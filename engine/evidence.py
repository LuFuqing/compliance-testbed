"""Evidence artifacts (EV1-EV6) and the cross-organisational handover bundle.

Domain-agnostic layer of the compliance-by-design simulation testbed.

Artifact -> standard mapping
  EV1 ClassificationLabel   <- GB/T 43697-2024  (data classification & grading)
  EV2 CryptoAttestation     <- GB/T 39786-2021  (cryptography application)
  EV3 AuditLog              <- GB/T 22239-2019  (classified protection, level 3)
  EV4 ModelSBOM             <- model supply-chain risk (Pillar D)
  EV5 HandoverReceipt       <- 20262810-T-907   (draft; PLAN NUMBER, not published)
  EV6 PIIRecord             <- PIPL + compliance-audit measures (2025-05-01)
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import List, Optional

DATA_CLASSES = ("general", "important", "core")
SENSITIVE_CLASSES = ("important", "core")


def h(*parts) -> str:
    """Deterministic hash used to simulate the evidence hash-chain."""
    m = hashlib.sha256()
    for p in parts:
        m.update(str(p).encode("utf-8"))
    return m.hexdigest()[:16]


@dataclass
class DataItem:
    data_id: str
    classification: str            # ground-truth class (auditor's truth)
    pii: bool = False
    value: float = 0.0


@dataclass
class ClassificationLabel:
    """EV1 - what the operator *declares* the data to be."""
    data_id: str
    label: str
    correct: bool = True


@dataclass
class CryptoAttestation:
    """EV2 - payload hash + signature (GB/T 39786)."""
    data_id: str
    payload_hash: str
    signed: bool
    key_id: str = "k1"


@dataclass
class AuditLog:
    """EV3 - access/operations audit trail (GB/T 22239)."""
    entries: List[str] = field(default_factory=list)


@dataclass
class ModelSBOM:
    """EV4 - model component provenance (Pillar D)."""
    components: List[str] = field(default_factory=list)


@dataclass
class HandoverReceipt:
    """EV5 - cross-organisational handover receipt (20262810-T-907, draft)."""
    chain_hash: str
    timestamp: float
    signer: str
    well_formed: bool = True
    tampered: bool = False


@dataclass
class PIIRecord:
    """EV6 - personal-information handling record (PIPL)."""
    data_id: str
    deidentified: bool
    consent: bool


@dataclass
class HandoverBundle:
    """One cross-organisational handover event + its evidence bundle."""
    item: DataItem
    ev1: ClassificationLabel
    ev2: CryptoAttestation
    ev3: AuditLog
    ev4: ModelSBOM
    ev5: HandoverReceipt
    ev6: PIIRecord
    # operator actions (derived from the *declared* label, not ground truth)
    encrypted_at_rest: bool = True
    local_storage: bool = True
    latency: float = 0.0
    verified: bool = False        # evidence completeness (M1)
    recovered: bool = False       # tampered receipt repaired via signed attestation (M5)
    # bookkeeping for the auditor
    injected: List[str] = field(default_factory=list)   # violation tags injected
    detected: List[str] = field(default_factory=list)   # rules that failed
