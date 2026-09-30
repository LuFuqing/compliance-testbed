# Changelog

All notable changes to the compliance-by-design simulation testbed are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is
[semantic](https://semver.org/spec/v2.0.0.html) with respect to the **public API of the
testbed** (`engine`, `ruleset`, `profiles`, `experiments`) — not to the numeric results,
which may legitimately shift when a modelled parameter is re-calibrated.

<!-- This heading is deliberately NOT written as "## [Unreleased]".  reproduce.sh reads the
     release date with  awk '/^## \[/{print $NF; exit}'  CHANGELOG.md, so a bracketed heading
     without a date would make the banner print "(released unknown)". -->
## Unreleased

Staged ahead of the deposit that accompanies the manuscript. **No numeric change**: the four
release fingerprints below are untouched, because nothing in this section reaches the
computation.

### Changed

- **The two experiment stages are no longer called `T9` and `T10`.** They are now named for what
  they run: the **scenario suite** (scenario comparison plus Morris screening) and the
  **stress and sensitivity suite** (the SL/T 853-855 process stress contrast, the Sobol
  decomposition, the supplementary tables and the figures). The manuscript never used the old
  labels — it says "scenario suite", "stress contrast" and "sensitivity analysis" — so this
  aligns the artifact with the paper's own vocabulary. Renamed with it:
  `run_t10.py` → `run_stress_sensitivity.py`; Makefile targets `t9` / `t10` → `scenario` /
  `stress`; `reproduce.sh` variables `T9_START` / `T10_START` / `T10_ARGS` → `SCEN_START` /
  `STRESS_START` / `STRESS_ARGS`; the verifier's check-group headings.
  Reading a historical entry below: `T9` = scenario suite, `T10` = stress and sensitivity suite.
- `docs/RESEARCH_DESIGN.md` added — the research design record: research questions, system
  model, the R1-R8 formalisation with weights, the simulation model, the experimental matrix,
  contributions and scope limits. Authored, not regenerated, and therefore outside `results/`.
- `README.md`: the "companion to" reference pointed at a research-design file that is not part
  of the artifact; it now points at `docs/RESEARCH_DESIGN.md`. The `docs/` tree was added to the
  repository layout listing and to the CC BY 4.0 documentation table in `NOTICE` and below.
- `README.md`: the internal labels `case (B)` / `probe (B')` / `contribution A|B` were replaced
  by plain wording. They referred to positions in an earlier planning document that the artifact
  does not ship, so a reader had no way to resolve them.
- `make_manifest.py`: `docs/` added to `SOURCE_DIRS`. The manifest's file list is an explicit
  whitelist rather than a walk of the artifact root, so a new top-level directory would have been
  distributed *and not digested* — with no failure, because `check()` uses that same list as its
  definition of "present". The comment above the lists now says so.

## [1.0.4] — 2026-09-23

Numeric release. It changes one estimator parameter, and with it the reported first-order
Sobol indices. Everything else — scenarios, metrics, seeds, random draws, counts and
intervals — is untouched, which is visible in the fingerprints: three of the four are byte-for
byte what they were in v1.0.3, and only `sobol.csv` moved. One figure changes for readability
only (legend placement, under Changed); the data it plots are identical.

**The binned conditional-mean estimator now uses 10 bins instead of 12.** Two things forced the
decision. First, a consistency failure: Table 7 panel A printed `0.990` for a single-factor
function, and no Seed reproduced that at 12 bins, because the estimator's large-N limit for such
a function is exactly `1 - 1/B^2` — 0.993 at B = 12, 0.990 at B = 10. The printed value was right
for ten bins while Section 4.4 said twelve, so the paper contradicted itself. Second, a reason of
substance: `n_stakeholders` takes exactly **ten** integer values in its range (3–12). At ten bins
every bin holds one distinct level, so that factor's conditional mean is a plain group mean with
no within-bin mixing; at twelve bins the ten levels spread across twelve bins, some empty and some
holding two levels, which biases that index. Ten is therefore not merely the count the printed
values were consistent with — it is the correct count for this design.

### Changed
- `experiments/sobol.py` gains **`DEFAULT_BINS = 10`**, now the single source of truth cited by
  `s1_binned()`, `run_sobol()`, `experiments/estimator_validation.py` (both panels) and
  `verify_results.py`. All five previously wrote `12` independently, which is how a parameter that
  changes published numbers came to have five owners.
- **Every S1 in `results/sobol.csv` moves down** by 0.003–0.006, and so does Σ S1 (M6 0.923 →
  0.910, M1 0.917 → 0.900). `n_stakeholders` moves most in relative terms, 0.0059 → 0.0019 and
  0.0050 → 0.0015, because it is the factor the change corrects. **ST is unchanged** — it is
  estimated by Saltelli/Jansen, which does not use binning — so ST − S1 rises to compensate, and
  Σ ST (1.078 / 1.083) is untouched.
- Nothing qualitative changes. The dominant factor stays `p_atk` for M6 and `p_skip` for M1, the
  control inversion survives, `p_err` remains the most interactive factor, and `n_stakeholders`
  remains a non-factor. Section 6.2's findings therefore still hold; only the digits move.
- `results/estimator_validation.csv` loses its duplicated bin counts. Panel A used to be emitted
  at both 12 and 10 because the two pairs of values were mutually inconsistent; with one bin count
  for the whole artifact it is emitted once, so the file goes from 28 rows to 20. Panel A is now
  **reproducible** from its recorded seed and is asserted to the digit, where before it could only
  be checked against the estimator's own seed-to-seed spread. Panel B's substituted column moves
  (additive 0.499/0.494 → 0.496/0.493, interaction 0.430/0.422 → 0.427/0.422, single factor
  0.993 → 0.990); its Saltelli and Jansen columns do not move at all.
- Golden checks go from **182 to 180**: eight checks existed only to police the 12/10 discrepancy
  and were replaced by stronger ones, including an assertion that panel A's single-factor index
  lands on the analytic ceiling `1 - 1/B²` for whatever `B` the artifact declares.
- The **release fingerprint for `sobol.csv` changes** to `24b3a2b0d6002dec6eb4c8c36cf8ad5a`. The
  other three are unchanged and still `0e7966af…`, `2c3fa6b7…`, `2e390879…`. Because these digests
  are the published record of what the numbers were, this is a new minor version rather than a
  patch: any reader who verified against v1.0.3 needs to be able to tell that the values moved.
- `experiments/figures.py`: the scenario-comparison figure's legend moves below the axes in
  three columns, where an in-axes legend overlapped the bars. `fig1_scenarios.png` is the only
  regenerated figure; the other three are byte-identical.

### Fixed
- `RESULTS.md` §2② said the transport closed form matched the measured ratios "exactly
  (14/24 and 13/28)"; 13/28 is 0.464, not the predicted 0.4167. Reworded to the manuscript's
  framing: the measured Wilson interval contains the prediction, and the sample does not resolve
  the predicted 0.167 gap. §2⑤ softened "predicted exactly" to match.
- `RESULTS.md` §5.1 quoted validation rows for `x0·x1` and `x0 + 9x1` that had no source
  anywhere in the artifact — no script computed them and no check asserted them, so they could
  not be reproduced. Removed, with a note saying why; the remaining two rows now name
  `results/estimator_validation.csv` as their source. A results document that asserts "these
  numbers are mechanical" cannot also carry numbers nothing computes.

## [1.0.3] — 2026-09-23

Additive release. It ships the three supplementary tables the manuscript's data-availability
statement promises, and it retires the last places where the repository's **runtime output**
still called the flood experiment a calibration after the documentation had stopped doing so.
No metric definition, parameter, seed or random draw changed, so the four data-file fingerprints
are unchanged and every number in `RESULTS.md` still holds.

The manuscript states that the supplementary material contains "the complete scenario
definitions, the full stress-contrast table with injected-mislabel counts and interval
estimates, sensitivity input and output samples, analytic validation of the sensitivity
estimators in both output regimes, and an archive manifest with SHA-256 digests", and that all
of it is regenerated by the same reproduction script as the main results. Three of those five
items had no generator in the tree: the counts and intervals behind M3s, the Sobol input/output
samples, and the estimator-validation table. They are now produced by `run_t10.py` and checked
by `verify_results.py`, so the statement is true of the artifact rather than of the manuscript's
intent.

### Added
- `results/stress_contrast.csv` — 22 rows: the six SL/T 853-855 process phases under the stressed
  and nominal control runs, plus the ten T9 scenarios, each with raw injection/detection counts,
  the mislabel counts behind M3s, and the two-sided 95% Wilson interval. Generator:
  `experiments/supplementary.py`. The counts are the sample sizes the manuscript now reports
  (stressed phases 3/7/8/16/42/4; nominal 3/2/3/7/7/1; S0 24/14; S1 183/106; transport 28/13).
- `results/sobol_samples.csv` — the sensitivity design's inputs and outputs in evaluation order:
  the 4000-row Monte-Carlo matrix behind the binned S1, the two 1024-row Saltelli base matrices,
  and one column-substituted matrix per factor (4 × 1024), both targets on every row. 10,144 rows.
  Written by `experiments/sobol.py` inside the same pass that computes the indices, so the samples
  and `sobol.csv` cannot disagree; the verifier recomputes S1 and ST from the file alone.
- `results/estimator_validation.csv` — Table 7 of the manuscript, one row per
  (panel, test function, factor), with the bin count and sample size recorded per row.
  Generator: `experiments/estimator_validation.py`.
- `results/SHA256SUMS` — the archive manifest, written by the new `make_manifest.py`, which
  `reproduce.sh` now calls. It digests every file under `results/` plus the source and metadata
  files. `python3 make_manifest.py --check` re-verifies it. `dist/SHA256SUMS` (from
  `make_release.py`) still covers the packaged archives and is a separate document.
- `engine/metrics.py` — `detection_counts(bundles)` and `wilson_interval(k, n)`. Both are purely
  additive: `compute()` is untouched, so no metric value moves.
- `experiments/calibration.py` / `experiments/run_scenarios.py` — an optional `sink` argument that
  additionally hands out the raw handover bundles. Does not affect the written output files.

### Changed
- The flood experiment is now called a **stress contrast** in every place the code speaks to a
  human, as well as in the documentation: the `run_t10.py` and `reproduce.sh` banners, the
  `calibration.py` and `flood_event.py` docstrings, and the verifier's section heading. This
  closes the gap left by 1.0.2, which fixed the prose but not the run-time output. The module and
  output file names (`experiments/calibration.py`, `results/calibration.csv`) are unchanged.
- `reproduce.sh` reads the artifact version from `VERSION` and the release date from the newest
  `CHANGELOG.md` entry instead of carrying its own copy, so the two cannot drift; it previously
  printed `v1.0.0` and `released 2026-09-19` while the artifact was v1.0.2. Two stale `v1.0.0`
  stamps were removed the same way: `verify_results.py` now prints the version it read.
- `verify_results.py` gained four check groups (stress contrast, Sobol samples, estimator
  validation, manifest) and reports the version it read from `VERSION`. Golden checks go from
  **120 to 182**; `./reproduce.sh --clean --strict` completes in about 21 s with all of them
  passing and the four data-file fingerprints unmoved.
- `make manifest` now writes `results/SHA256SUMS` via `make_manifest.py`; the MD5 drift report
  that used to own that name moved to `make fingerprints`. `make all` writes the manifest before
  verifying, because the verifier checks it.
- `make_release.py` now runs `make_manifest.py --check` before staging and **refuses to package a
  tree whose manifest is stale**, exiting non-zero with the mismatching paths. `--force` bypasses
  it. The build order is therefore `./reproduce.sh` first, `make release` second, and the same
  precondition is documented in `README.md`, `RELEASE.md` and the `Makefile` header.

### Fixed
- A 1.0.3 archive was built from a tree whose `results/estimator_validation.csv` had been
  regenerated *after* `results/SHA256SUMS` was written, so the package shipped a manifest that
  did not describe its own contents (`experiments/estimator_validation.py` and
  `results/estimator_validation.csv` both mismatched) and would have failed
  `make_manifest.py --check` on unpacking. `make_release.py` collected whatever was on disk and
  never consulted the manifest, which is how the drift rode in. Caught by re-running
  `make_manifest.py --check` on the live tree; fixed by rebuilding the archives from a fresh
  reproduction run, and prevented from recurring by the precondition above. **The previously
  recorded 1.0.3 archive digests are superseded**; `dist/SHA256SUMS` now carries the rebuilt ones.

### Notes for the reader
- `estimator_validation.csv` records the **bin count** per row because the binned first-order
  estimator is not bin-count invariant: for a single-factor function its large-N limit is exactly
  `1 - 1/B^2`, i.e. 0.993 at B = 12 and 0.990 at B = 10. Panel A is emitted at both, because the
  two substituted-S1 values printed in Table 7 of the manuscript are consistent only with B = 10,
  while Section 4.4 stated B = 12 for the substitution at the time of v1.0.3. This discrepancy was
  reconciled at v1.0.4: the manuscript now states ten equiprobable bins, so its reported Sobol
  indices (Table 9/10) are consistent with the declared estimator and with the Table 7 B = 10
  values. The table's own bin count and the estimator's seed-to-seed spread are reported
  alongside, so the bin-count sensitivity is visible rather than hidden. Nothing in the artifact
  depends on the bin count; it is a reported, validated parameter.
- The additive function's first factor has a seed-to-seed standard deviation of about 0.011 --
  wider than the three decimals Table 7 prints -- so `ensemble_mean` and `ensemble_sd` over 200
  independent matrices are reported next to each single-seed value.

## [1.0.2] — 2026-09-20

Documentation-only release. No code, rule, profile or result value changed, so the four
data-file fingerprints of v1.0.0 remain valid and every number in `RESULTS.md` is unchanged.

The accompanying manuscript went through a five-seat review whose central requirement was to
separate **encoding claims** (consequences of how a rule or metric is written), **mechanism
claims** (consequences of how the simulated agents interact) and **target claims** (statements
about real cities or about the standards). Several statements in this repository's documentation
were encoding consequences presented as research findings, and after the manuscript revision they
contradicted it. This release brings the documentation into line.

### Fixed
- `RESULTS.md` still carried a stale **115** in its header. The 1.0.1 fix corrected only the copy
  in §6, so the file disagreed with itself; both now read **120**.

### Changed
- `RESULTS.md` now states the **claim-type discipline** up front, and §2② gives the **closed
  form** of the silent-misclassification rate
  (`M3s = 1 - (1/N) * sum s(c_i)`, with s = 1, 1/2, 0 for general/important/core) instead of
  reading the ~0.58 plateau as a discovery. Flood 1/3/2 gives 0.5833 and transport 2/3/1 gives
  0.4167, matching the measured 14/24 and 13/28.
- The claim that this plateau represents a **gap in the standards is withdrawn**. It follows from
  R1 checking label *presence* rather than *correctness*, so the derivable statement is a
  **recommendation to standard-writers**, not a measurement of their output.
- The headline is restated as the **divergence between conformance and verifiability** (B1 passes
  54.4% of the weighted rule set while producing zero replayable handovers). The previous
  "signed receipt is the decisive control" framing survives only with the explicit admission that
  M1's zero is **definitional**.
- The flood experiment is consistently called a **stress contrast**, never a calibration: the load
  and the stress profile are both analyst-assigned in one table, so the correlations (+0.810,
  +0.835) are a **coherence check on that assignment**, not a regularity discovered in data.
- **Claim withdrawn:** M3s "collapses under load" (0.667 → 0.429/0.500 → 0.690). Re-examined, every
  stressed phase's Wilson 95% interval **contains** the closed-form 0.5833; the apparent collapse
  was sampling noise at n = 3–8 injected mislabels. Per-phase counts and intervals are now given.
- M5 is reported as 1.000 **in every stressed phase in which an attack occurred (P1–P5)**; P0 is
  **undefined**, where the file previously implied 1.000.
- Topology/scale invariance is described as **constructional** — those parameters enter the engine
  only through the latency term — rather than as an empirical robustness result, and profile
  substitution is described as **interface portability** rather than cross-domain validity.
- `M2` is named **modelled evidence-reconstruction cost (arbitrary units)** throughout. It is not
  wall-clock or person-day time, and the earlier reading of it as audit preparation effort is gone.
- Sobol documentation adds the **low-variance validation** of the substituted estimator (at
  sd ≈ 0.012 the classic Saltelli S1 returns 1.155/0.972 additive and 1.927 single-factor) and
  discloses its **upward bias under pure interaction** (~0.43 attributable for a true zero), so
  reported S1 values are upper bounds. The `n_stakeholders` interaction entries are given as
  −0.006 / −0.005 instead of "~0", and Σ ST = 1.078 / 1.083 is disclosed.
- `README.md`: version references updated to 1.0.2; the verifier's claim list, the M2/T10/M5
  wording and the extractor note aligned with `RESULTS.md`.
- `CITATION.cff`: `version` was still `1.0.0` after the 1.0.1 release — corrected, with the
  abstract's version string and stress-contrast wording aligned.

## [1.0.1] — 2026-09-19

Documentation-only release. No code, rule, profile or result value changed, so the four
data-file fingerprints of v1.0.0 remain valid.

### Fixed
- `RESULTS.md` stated **115** golden checks; the verifier reports **120**. The count is
  accumulated at run time, and the documented figure was stale. Corrected to 120.

### Changed
- The 36-hour flood event is described as **synthetic** rather than "de-identified"
  (`README.md`, `RESULTS.md`, `CHANGELOG.md`). The data was always generated from a seeded
  pseudo-random stream; "de-identified" implied a real record had been anonymised, which was
  never the case.

## [1.0.0] — 2026-09-19

First public release, accompanying the manuscript submission.

### Added
- `engine/` — domain-agnostic simulation core: evidence artifacts EV1–EV6 and the
  `HandoverBundle`, five agent roles (Source, Operator, Attacker, Agency, Auditor), the
  seeded discrete-event loop, and metrics M1–M6.
- `ruleset/rules.py` — the R1–R8 machine-checkable predicates anchored in GB/T 43697-2024,
  GB/T 39786-2021, GB/T 22239-2019 (L3), 20262810-T-907 (draft; plan number), PIPL and the
  compliance-audit measures; profile-independent and shared by all domains.
- `profiles/` — `flood` (SL/T 853-855 validation case) and `transport` (cross-domain
  generalisation probe), behind a common `Profile`/`SourceSpec` interface.
- `experiments/run_scenarios.py` — baselines B0/B1 and scenarios S0–S6b.
- `experiments/sensitivity.py` — Morris elementary-effects screening.
- `experiments/sobol.py` — Sobol decomposition using a **binned conditional-mean estimator
  for S1** (the classic Saltelli S1 estimator is unusable on this low-variance output) and
  Saltelli/Jansen for ST; validated against analytic functions with known indices.
- `experiments/flood_event.py`, `experiments/calibration.py` — the synthetic 36-hour
  urban flood event and its SL/T 853-855 phase stress contrast (stressed vs nominal control).
- `experiments/figures.py` — figures 1–4 at 300 dpi (requires matplotlib).
- `reproduce.sh`, `verify_results.py`, `Makefile` — one-click reproduction and
  golden-value verification.
- Dual licensing: MIT for code, CC BY 4.0 for data, figures and documentation.

### Known limitations
- All scenario data are **synthetic** (seed 42). The stress/load coupling in the flood event
  is an analyst-assigned parameterisation, not a measurement from an operational response.
- 20262810-T-907 is a **draft identified by its plan number**; it is used as a label only.
- M2 is a modelled evidence-reconstruction cost in arbitrary units, not wall-clock time.
- M3s (silent-misclassification detection) sits near 0.58 under full design. This is an
  **encoding property of R1**, given in closed form; see the 1.0.2 entry above.
