"""Domain-agnostic agents: Source, Operator, Attacker, Agency, Auditor.

Modes
  B0  no compliance-by-design   (no labels / signing / receipt / audit / PII handling)
  B1  partial design            (labels + encryption + audit only)
  B2  full compliance-by-design (R1-R8 enforced; error probabilities apply)
"""
from __future__ import annotations

import random
from typing import List

from engine.evidence import (AuditLog, ClassificationLabel, CryptoAttestation,
                             DataItem, HandoverBundle, HandoverReceipt, ModelSBOM,
                             PIIRecord, SENSITIVE_CLASSES, DATA_CLASSES, h)


class Source:
    """A physical sensing entity emitting data items."""

    def __init__(self, spec, rng: random.Random):
        self.spec = spec
        self.rng = rng
        self.counter = 0

    def emit(self, t: int) -> DataItem:
        self.counter += 1
        return DataItem(
            data_id=f"{self.spec.source_id}-{t:04d}-{self.counter}",
            classification=self.spec.data_class,
            pii=self.spec.pii,
            value=round(self.rng.random(), 4),
        )


class Operator:
    """The digital-twin operator: classifies, encrypts, signs, issues receipts."""

    def __init__(self, profile, params, rng: random.Random):
        self.profile = profile
        self.params = params
        self.rng = rng

    def process(self, item: DataItem, t: int) -> HandoverBundle:
        p = self.params
        rng = self.rng
        mode = p.mode
        injected: List[str] = []

        # ---- EV1 classification label ------------------------------------
        if mode == "B0":
            declared = ""                                  # no label at all
        elif mode == "B1":
            declared = item.classification                 # correct, but no signing
        else:                                              # B2
            if rng.random() < p.p_err:
                others = [c for c in DATA_CLASSES if c != item.classification]
                declared = rng.choice(others)
            else:
                declared = item.classification
        correct = (declared == item.classification)
        if mode != "B0" and not correct:
            injected.append("mislabel")
        ev1 = ClassificationLabel(item.data_id, declared, correct)

        # ---- operator actions driven by the *declared* label -------------
        if mode == "B0":
            encrypted_at_rest = False
            local_storage = False
        else:
            encrypted_at_rest = declared in SENSITIVE_CLASSES
            local_storage = (declared == "core")

        # ---- EV2 crypto attestation --------------------------------------
        if mode in ("B0", "B1"):
            signed = False
        else:
            signed = rng.random() >= p.p_skip
        if not signed:
            injected.append("unsigned")
        ev2 = CryptoAttestation(item.data_id, h(item.data_id, item.value), signed)

        # ---- EV3 audit log -----------------------------------------------
        if mode == "B0":
            entries: List[str] = []
        elif mode == "B1":
            entries = [f"access:{item.data_id}"]
        else:
            entries = [] if rng.random() < p.p_noaudit else [f"access:{item.data_id}"]
        if not entries:
            injected.append("no_audit")
        ev3 = AuditLog(entries)

        # ---- EV4 model SBOM ----------------------------------------------
        ev4 = ModelSBOM(list(self.profile.models))

        # ---- EV5 handover receipt ----------------------------------------
        if mode == "B0":
            ev5 = HandoverReceipt("", 0, "", well_formed=False)
        elif mode == "B1":
            ev5 = HandoverReceipt(h(item.data_id, t), float(t), "", well_formed=False)
        else:
            ev5 = HandoverReceipt(h(item.data_id, t, signed), float(t), "operator",
                                  well_formed=True)
        if not ev5.well_formed:
            injected.append("no_receipt")

        # ---- EV6 PII handling (PIPL) -------------------------------------
        if mode == "B2" and item.pii:
            fail = rng.random() < p.p_pii_fail
            deid, consent = (not fail), (not fail)
        else:
            deid, consent = False, False
        ev6 = PIIRecord(item.data_id, deid, consent)

        # ---- cross-cutting injections (ground-truth based) ---------------
        if not encrypted_at_rest and item.classification in SENSITIVE_CLASSES:
            injected.append("no_encrypt")
        if not local_storage and item.classification == "core":
            injected.append("nonlocal")
        if item.pii and not (deid and consent):
            injected.append("pii_unhandled")

        return HandoverBundle(item=item, ev1=ev1, ev2=ev2, ev3=ev3, ev4=ev4,
                              ev5=ev5, ev6=ev6, encrypted_at_rest=encrypted_at_rest,
                              local_storage=local_storage, injected=injected)


class Attacker:
    """Adversary: tampers with / replays the handover receipt (EV5)."""

    def __init__(self, params, rng: random.Random):
        self.params = params
        self.rng = rng

    def tamper(self, b: HandoverBundle) -> None:
        b.ev5.tampered = True
        b.injected.append("tamper")


class Agency:
    """Receiving organisation: verifies the evidence chain."""

    def verify(self, b: HandoverBundle) -> bool:
        # M1 completeness: receipt well-formed, untampered, signed, EV2 valid
        b.verified = bool(b.ev5.well_formed and not b.ev5.tampered
                          and b.ev5.signer and b.ev2.signed)
        # M5 resilience: a *signed* attestation (EV2) lets the receiver detect a
        # tampered receipt and re-derive it. Only compliance-by-design can recover.
        b.recovered = bool(b.ev5.tampered and b.ev2.signed and b.ev5.well_formed)
        return b.verified


class Auditor:
    """Regulator / auditor: applies R1-R8 to reconstruct and score the evidence."""

    def __init__(self, ruleset):
        self.ruleset = ruleset

    def evaluate(self, b: HandoverBundle):
        results = self.ruleset.evaluate(b)
        b.detected = [r for r in self.ruleset.RULES if not results[r].passed]
        return results
