# Compliance-by-Design Simulation Testbed for City Digital Twins

**Version 1.0.4** · released 2026-09-23 · code under MIT, data and figures under CC BY 4.0

A domain-agnostic simulation testbed that formalises **China's data-security standards** as
machine-checkable constraints, and measures what *compliance-by-design* actually buys for
cross-organisational evidence handover in city digital twins. It ships a reusable engine, a
standard-anchored rule set, and two domain profiles: a **flood twin** as the validation case
and an **urban transport twin** as the cross-domain generalisation probe.

This artifact is the companion to [`docs/RESEARCH_DESIGN.md`](docs/RESEARCH_DESIGN.md), which states
the research questions, the system model, the rule formalisation R1-R8 and the experimental design
that this code implements; it supplies the empirical chapter of the accompanying manuscript.

---

## Download and one-click reproduction

```bash
unzip compliance_testbed-1.0.4.zip      # or: tar xzf compliance_testbed-1.0.4.tar.gz
cd compliance_testbed-1.0.4
./reproduce.sh
```

That single command runs the whole experiment chain and then **verifies** it: it re-derives
every reported number from scratch and asserts each one against the values quoted in
[`RESULTS.md`](RESULTS.md). **Exit code 0 means the paper's numbers were reproduced on your
machine, not just that the code ran.** On the release machine this takes about 21 seconds.

| Command | What it does |
|---|---|
| `./reproduce.sh` | scenario suite + stress/sensitivity + supplementary tables + manifest + figures + verification. The default, and what you want. |
| `./reproduce.sh --strict` | As above, but a mismatch in the release fingerprints fails the run. |
| `./reproduce.sh --clean` | Deletes `results/` first, then rebuilds everything from zero. |
| `./reproduce.sh --install-deps` | Creates `./.venv` and installs matplotlib, then runs the full chain. |
| `./reproduce.sh --no-figures` | Skips figure generation entirely (no matplotlib needed). |
| `./reproduce.sh --python /path/to/python` | Forces a specific interpreter. |
| `python3 make_manifest.py --check` | Re-verifies `results/SHA256SUMS` without a full run. |
| `python3 make_release.py` | Builds `dist/*.zip` and `dist/*.tar.gz`; refuses to package a stale manifest. |
| `make help` | Lists the equivalent `make` targets. |

Only the standard library is required for the numbers. **matplotlib is the single optional
dependency**, needed solely to re-render figures 1–4; without it `reproduce.sh` still rebuilds
and verifies every number but reports `REPRODUCTION: PARTIAL` so the gap is never silent.

Two scripts do the work:

- **`reproduce.sh`** — environment check, scenario suite, stress and sensitivity, verification, in that order.
- **`verify_results.py`** — the gate. It performs 180 golden checks (counted at run time)
  covering the substantive claims of the paper (the conformance/verifiability divergence, the
  closed-form silent-misclassification rate, the constructed topology/scale invariance, the
  stress contrast and its gap, and the Sobol control inversion), checks that the supplementary
  tables agree with the metrics and with each other, recomputes the Sobol indices from
  `sobol_samples.csv`, validates that figures 1–4 are genuine PNGs, verifies the SHA-256
  manifest, and reports MD5 fingerprints of the four generated CSVs so unintended drift is
  caught rather than published.

Because the archive ships both the code **and** the pre-computed results, you can also audit the
reported values without running anything at all — read `RESULTS.md` against `results/*.csv`.

## Why it exists

The literature pool backing the review shows three gaps this testbed is built to address:

- **evidence poverty** — frameworks outnumber empirical or validation studies by ~3.9:1;
- **China-standards asymmetry** — only 2.1% of records are Chinese-language, despite China's
  dense 2024–2026 standards output;
- **Pillar E thinness** — cross-organisational evidence handover is the thinnest pillar of the
  taxonomy (3.0% primary coverage, RQ5 at 8.0%).

The response is a testbed whose rule set is *anchored in citable Chinese standards* rather than
in a generic checklist, and whose generality is *demonstrated by a second domain* rather than
asserted.

## Architecture (`engine` / `ruleset` / `profiles` separation)

```
compliance_testbed/
  engine/          # domain-agnostic
    evidence.py    #   EV1-EV6 artifacts + HandoverBundle
    agents.py      #   Source, Operator, Attacker, Agency, Auditor
    simulator.py   #   Params + discrete-event loop
    metrics.py     #   M1-M6
  ruleset/
    rules.py       #   R1-R8 (shared truth source; profile-independent)
  profiles/
    base.py        #   Profile / SourceSpec interface
    flood.py       #   flood water twin  -> primary validation case
    transport.py   #   urban transport   -> cross-domain generalisation probe
  experiments/
    run_scenarios.py        # S0-S6 + B0/B1 baselines
    sensitivity.py          # Morris elementary-effects screening
    sobol.py                # Sobol S1 (binned conditional mean) + ST (Saltelli/Jansen)
                            #   also writes results/sobol_samples.csv
    flood_event.py          # 36 h synthetic flood event, SL/T 853-855 phases
    calibration.py          # stress contrast: stressed vs nominal control
                            #   (file name retained; the experiment is a contrast, not a calibration)
    supplementary.py        # supplementary tables from the availability statement
    estimator_validation.py # Table 7: both output regimes
    figures.py              # fig1-fig4 (matplotlib)
  run_all.py                  # scenario-suite entry point (scenarios + Morris)
  run_stress_sensitivity.py   # stress-and-sensitivity entry point (contrast + Sobol + tables + figures)
  reproduce.sh       # one-click reproduction
  verify_results.py  # golden-value verification
  Makefile           # make all/verify/fingerprints/manifest/release/clean
  make_release.py    # builds dist/*.zip and dist/*.tar.gz
  make_manifest.py   # writes results/SHA256SUMS
  RESULTS.md         # authored interpretation  (NOT regenerated)
  docs/
    RESEARCH_DESIGN.md  # research design, rule formalisation, experimental design (authored)
  results/           # generated data + figures   (fully regenerated)
```

**The engine and R1–R8 never change between domains** — only the profile swaps. That is what
makes the framework contribution claimable and testable through the case study. Be precise
about what the swap demonstrates: **interface portability** — the engine and rules can be driven
by a different profile without code changes. Similarity of the resulting numbers is largely
guaranteed by construction, because a profile carries only a bounded set of facts. It is not a
demonstration that the same numbers hold in a real transport twin (see `RESULTS.md` §2⑤ and §6).

Note the deliberate split between `RESULTS.md` at the root and everything under `results/`:
`results/` is regenerable in its entirety, `RESULTS.md` is hand-written interpretation. Keeping
the authored document outside the generated directory is what makes `--clean` safe.

## Rule set R1–R8 → standard anchors

| Rule | Standard | Requirement |
|---|---|---|
| R1 | GB/T 43697-2024 | every data item carries a class label |
| R2 | GB/T 43697-2024 | core data encrypted + audited + stored locally |
| R3 | GB/T 39786-2021 | important/core data encrypted at rest |
| R4 | GB/T 39786-2021 | evidence cryptographically signed |
| R5 | GB/T 22239-2019 (L3) | full-link access audit log |
| R6 | GB/T 22239-2019 (L3) | data integrity (chain untampered) |
| R7 | 20262810-T-907 (**draft; plan number**) | cross-org handover receipt (hash+ts+signer) |
| R8 | PIPL / compliance-audit measures | PII de-identified + consent |

> 20262810-T-907 is a **draft (plan number), not a published standard**. It is used as a label
> only; no clause is asserted to be in force. See `RESULTS.md` §6 for the full caveat list.

## Evidence artifacts (EV1–EV6)

EV1 classification label · EV2 crypto attestation · EV3 audit log · EV4 model SBOM ·
EV5 handover receipt · EV6 PII handling record.

## Modes

| Mode | Meaning |
|---|---|
| B0 | no compliance-by-design (no labels / signing / receipt / audit / PII handling) |
| B1 | partial design (labels + encryption + audit only) |
| B2 | full compliance-by-design (R1–R8 enforced; error probabilities apply) |

## Metrics

| Metric | Definition | Better |
|---|---|---|
| M1 | evidence completeness (valid, replayable receipts) | high |
| M2 | modelled evidence-reconstruction cost (**arbitrary units**) | low |
| M3 | violation detection rate | high |
| M3s | misclassification (silent-channel) detection | high |
| M4 | mean handover latency | low |
| M5 | tamper resilience (recovered after attack) | high |
| M6 | weighted conformance score over R1–R8 | high |

## Stress contrast and sensitivity

**Stress contrast (not a calibration).** `experiments/flood_event.py` encodes a *synthetic
36-hour urban flood event* as six phases aligned to the SL/T 853-855 process (data baseplate →
model → early warning → dispatch → recession). Each phase carries an evidence load and a
control-stress profile; the **stressed** run applies that stress, the **nominal** run keeps
fair-weather control quality at the same loads, so the difference isolates stress at fixed
workload.

Both the load and the stress profile are **assigned by the analyst in the same table**, and the
stress profile moves three parameters together. Nothing is fitted to observed data, so the
experiment is a *scenario contrast under an assumed coupling*, and the reported correlations are
a coherence check on that assignment rather than a regularity found in data. Treating the result
as a calibration — as earlier documentation did — overstated it. SL/T 853-855 supplies the
*reading* of the phases, not the load or stress values.

The hydrograph is **constructed** to be *in phase with the operational stages*, not with the
rainfall: level peaks at 5.600 m at t = 22 h (inside the dispatch phase), with the 4.5 m / 5.2 m
thresholds exceeded 16–27 h and 19–25 h respectively.

**Estimator note (important for reuse).** M6 has a very small output variance, so the classic
Saltelli first-order estimator is unusable here — it returns S1 > 1 and negative indices, and at
M6's own variance scale (sd ≈ 0.012) it returns 1.155/0.972 for an additive function and 1.927
for a single-factor one. `sobol.py` therefore uses a **binned conditional-mean estimator** for S1
(`S1_i ~= Var_bins(E[Y | X_i in bin]) / Var(Y)`, 10 equiprobable bins, N = 4000), validated on
analytic functions with known indices (additive, pure-interaction, single-factor, mixed-scale).

**The binned estimator is itself biased upward under pure interaction** — on a function whose
true first-order effect is zero it still attributes ~0.43. Reported S1 values are therefore
**upper bounds**, and the small negative ST − S1 entries are an artefact of the 180-handover
evaluation budget, not evidence of negative interaction. ST is kept as Saltelli/Jansen, which is
stable. **Any reuse of this module on a low-variance target must keep this substitution and this
caveat.**

**The bin count is not cosmetic.** The binned estimator is *not* bin-count invariant: for a
single-factor function its large-N limit is exactly `1 − 1/B²`, so B = 12 gives 0.993 and B = 10
gives 0.990. This artifact uses **ten** bins everywhere — held in `DEFAULT_BINS` in
`sobol.py`, and cited by `s1_binned()`, `run_sobol()`, both panels of `estimator_validation.py`
and the verifier rather than retyped in each. Recognising this is what let panel A of Table 7 be
reproduced at all: until v1.0.4 those rows were a value nobody could regenerate, because the paper
stated twelve bins and an unrecorded Monte-Carlo draw ten. `results/estimator_validation.csv`
records the bin count as a column rather than a footnote. Ten is also the count that suits this
design: `n_stakeholders` takes exactly ten integer values in its range, so every bin holds one
distinct level. **Changing `DEFAULT_BINS` changes `results/sobol.csv` and therefore the published
numbers, the release fingerprint and the version** — see the 1.0.4 changelog entry.

## Supplementary tables

The manuscript's data-availability statement promises five items, and all five are regenerated by
`./reproduce.sh`:

| Item | File | Producer |
|---|---|---|
| complete scenario definitions | `results/scenarios.csv`, `results/scenarios.json` | `run_all.py` |
| stress-contrast table with injected-mislabel counts and interval estimates | `results/stress_contrast.csv` | `run_stress_sensitivity.py` |
| sensitivity input and output samples | `results/sobol_samples.csv` | `run_stress_sensitivity.py` |
| analytic validation of the estimators in both output regimes | `results/estimator_validation.csv` | `run_stress_sensitivity.py` |
| archive manifest with SHA-256 digests | `results/SHA256SUMS` | `reproduce.sh` → `make_manifest.py` |

Two of these are worth reading before reusing the numbers:

- **`stress_contrast.csv`** carries the sample sizes the misclassification rate rests on. The
  stressed phases inject 3, 7, 8, 16, 42 and 4 mislabels, so the per-phase M3s values between
  0.429 and 0.750 are binomial noise on single-digit samples — every stressed phase's 95% Wilson
  interval contains the closed-form 0.583. This is the evidence behind the manuscript's withdrawn
  claim that the silent channel widens under load, and the verifier checks it explicitly.
- **`sobol_samples.csv`** is self-sufficient: the verifier recomputes S1 and ST from this file
  alone, by the same estimators, and asserts they match `sobol.csv`. If the samples and the
  indices ever disagree, the check fails.

`dist/SHA256SUMS` (from `make_release.py`) is a different document: it digests the packaged
archives, not the tree. `results/SHA256SUMS` digests the tree.

`make_release.py` runs `make_manifest.py --check` before staging and refuses to package a tree
whose manifest is stale, because the archive carries whatever is on disk and a leftover manifest
would otherwise ride in. Run `./reproduce.sh` before `make release`; `--force` bypasses the check.

## Scenario map

`B0_none`, `B1_partial`, `S0_full_baseline`, `S1_mislabel_high`, `S2_unsigned_high`,
`S3_mesh_topology`, `S4_adversarial`, `S5_scale_N12`,
`S6_transport_baseline` (profile swap), `S6b_transport_adv`.

## Reproducibility

All runs are seeded (`Params.seed = 42`), so results are deterministic: a rerun on a different
machine reproduces the shipped CSVs byte-for-byte, which is why `verify_results.py` can treat
their MD5 digests as release fingerprints. Figures are regenerated at 300 dpi.

`make fingerprints` prints the MD5 fingerprint manifest; `make manifest` writes the SHA-256
archive manifest and `make manifest-check` re-verifies it; `make verify` runs the checks alone;
`./reproduce.sh --strict` turns any fingerprint drift into a failure.

If you deliberately re-calibrate a modelled parameter, the golden checks will fail by design —
that is the mechanism that forces `RESULTS.md` to be reviewed instead of silently invalidated.
Refresh the fingerprints in `verify_results.py` only after confirming the new numbers.

## Requirements

- **Python 3.9+**, standard library only, for the full numbers.
- **matplotlib** (optional) only to re-render figures 1–4. `./reproduce.sh --install-deps`
  will create `./.venv` and install it for you.
- No other dependencies, no network access required, no build step.

## Citation

If you use this testbed, its rule set, or its reported results, please cite it. Machine-readable
metadata is in [`CITATION.cff`](CITATION.cff).

```bibtex
@software{lu2026compliance,
  author  = {Lu, Fuqing},
  title   = {Compliance-by-Design Simulation Testbed for City Digital Twins
             Under China's Data-Security Standards},
  version = {1.0.4},
  year    = {2026},
  date    = {2026-09-23},
  license = {MIT AND CC-BY-4.0},
  doi     = {<DOI>}
}
```

## Licence

Dual-licensed by content type, because code and evidence have different reuse needs:

| Material | Licence | File |
|---|---|---|
| Code (`engine/`, `ruleset/`, `profiles/`, `experiments/`, entry points, scripts, Makefile) | MIT | [`LICENSE`](LICENSE) |
| Data, figures, documentation (`results/`, `RESULTS.md`, `docs/`, `README.md`, `CHANGELOG.md`) | CC BY 4.0 | [`LICENSE-DATA`](LICENSE-DATA) |

In short: the code may be used, modified and redistributed commercially with attribution; the
data and figures may be shared and adapted, including commercially, with attribution. The exact
scope per path is spelled out in [`NOTICE`](NOTICE). The CC BY 4.0 legal code is vendored in
full so the archive is self-contained offline.

Change log: [`CHANGELOG.md`](CHANGELOG.md). Packaging and deposit instructions:
[`RELEASE.md`](RELEASE.md).

## Status and limitations

This is a **v1.0.4 research artifact under manuscript submission**, not a certified tool. **No real
data are used**: the scenario data and the flood event are synthetic, and the load/stress values
are assigned by the analyst rather than measured from an operational response. The five roles run
in a single process sharing one seed stream, so cross-organisational behaviour is modelled, not
exercised. 20262810-T-907 is cited as a **draft plan number**. `RESULTS.md` §6 lists the
limitations in full; please read it before reusing the numbers.
