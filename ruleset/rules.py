"""R1-R8: China data-security standards formalised as machine-checkable predicates.

The rule set is **domain-agnostic** - it is the shared truth source consumed by the
engine's Auditor agent and is identical across every domain profile.  A profile only
decides *which* data items are important/core and which carry PII.

Rule   Standard anchor          Requirement
----   ----------------------   ---------------------------------------------------
R1     GB/T 43697-2024          every data item carries a class label
R2     GB/T 43697-2024          core data: encrypted + audited + stored locally
R3     GB/T 39786-2021          important/core data encrypted at rest
R4     GB/T 39786-2021          evidence cryptographically signed (hash + key)
R5     GB/T 22239-2019 (L3)     full-link access audit log present
R6     GB/T 22239-2019 (L3)     data integrity check (chain not tampered)
R7     20262810-T-907 (draft)   cross-org handover produces a receipt (hash+ts+signer)
R8     PIPL / audit measures     PII de-identified + consent recorded
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from engine.evidence import HandoverBundle, DATA_CLASSES, SENSITIVE_CLASSES

RULES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]

# relative weight of each rule in the conformance score M6
WEIGHTS = {"R1": 1.0, "R2": 1.5, "R3": 1.0, "R4": 1.5,
           "R5": 1.0, "R6": 1.0, "R7": 1.5, "R8": 1.0}

ANCHORS = {
    "R1": "GB/T 43697-2024",
    "R2": "GB/T 43697-2024",
    "R3": "GB/T 39786-2021",
    "R4": "GB/T 39786-2021",
    "R5": "GB/T 22239-2019",
    "R6": "GB/T 22239-2019",
    "R7": "20262810-T-907 (draft)",
    "R8": "PIPL / audit measures",
}


@dataclass
class RuleResult:
    rule: str
    passed: bool
    detail: str = ""


def evaluate(bundle: HandoverBundle) -> Dict[str, RuleResult]:
    """Evaluate R1-R8 against a single handover bundle (the auditor's predicate)."""
    res: Dict[str, RuleResult] = {}

    # R1 - classification label present and well-formed
    res["R1"] = RuleResult("R1", bundle.ev1.label in DATA_CLASSES,
                           "class label present")

    # R2 - core data must be encrypted, audited and stored locally
    if bundle.item.classification == "core":
        ok = (bundle.encrypted_at_rest
              and len(bundle.ev3.entries) > 0
              and bundle.local_storage)
    else:
        ok = True
    res["R2"] = RuleResult("R2", ok, "core data encrypted+audited+local")

    # R3 - important/core data encrypted at rest (ground truth decides)
    if bundle.item.classification in SENSITIVE_CLASSES:
        ok = bundle.encrypted_at_rest
    else:
        ok = True
    res["R3"] = RuleResult("R3", ok, "sensitive data encrypted at rest")

    # R4 - evidence signed (crypto attestation + receipt signer, untampered)
    ok = bundle.ev2.signed and bool(bundle.ev5.signer) and not bundle.ev5.tampered
    res["R4"] = RuleResult("R4", ok, "evidence cryptographically signed")

    # R5 - audit log present
    res["R5"] = RuleResult("R5", len(bundle.ev3.entries) > 0, "audit log present")

    # R6 - integrity (well-formed, untampered receipt)
    res["R6"] = RuleResult("R6", bool(bundle.ev5.well_formed) and not bundle.ev5.tampered,
                           "integrity check")

    # R7 - handover receipt well-formed (hash chain + timestamp + signer)
    ok = bool(bundle.ev5.chain_hash) and bundle.ev5.timestamp > 0 and bool(bundle.ev5.signer)
    res["R7"] = RuleResult("R7", ok, "handover receipt (hash+ts+signer)")

    # R8 - PII de-identified + consent
    if bundle.item.pii:
        ok = bundle.ev6.deidentified and bundle.ev6.consent
    else:
        ok = True
    res["R8"] = RuleResult("R8", ok, "PII de-identified + consent")

    return res


def conformance_score(results: Dict[str, RuleResult]) -> float:
    """M6 - weighted pass rate over R1-R8 (0..1)."""
    num = sum(WEIGHTS[r] * (1.0 if results[r].passed else 0.0) for r in RULES)
    den = sum(WEIGHTS.values())
    return num / den
