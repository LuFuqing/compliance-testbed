# Release and deposit guide

This document is for whoever is **publishing** the testbed, not for whoever is *using* it.
Users should read [`README.md`](README.md) and run `./reproduce.sh`.

---

## 1. Before you publish — checklist

Work through this list in order. Nothing here is optional if the artifact is to be cited in a
paper, because a reviewer may check any of it.

### 1a. The automated gate

- [ ] **Re-run the full chain and confirm it verifies.**
      ```bash
      ./reproduce.sh --clean --strict
      ```
      It must end with `REPRODUCTION: SUCCESS` and `RESULT: PASS -- 180 golden checks passed,
      0 failed`. `--strict` additionally makes fingerprint drift fatal.
- [ ] **Confirm figures were actually regenerated**, not skipped. The run prints
      `matplotlib ... present - figures will be regenerated`; if it says `PARTIAL` instead,
      install matplotlib (`./reproduce.sh --install-deps`) and repeat.
- [ ] **Confirm the archive manifest is clean.**
      ```bash
      python3 make_manifest.py --check
      ```
      It must print `MANIFEST: OK` with one entry per file in `results/` plus the source tree.

### 1b. Placeholders — find every one, in one command

The release metadata contains placeholders that only the author can fill. **The verifier lists
them as `[WARN]` on every run**, so a stale placeholder cannot be published unnoticed. To list
them yourself (this file is excluded on purpose — it names the placeholders by construction):

```bash
for f in CITATION.cff NOTICE README.md Makefile; do
  grep -n 'CHANGEME\|<DOI\|<REPOSITORY-URL>' "$f"
done
```

As of v1.0.4 there were five, and all five are now resolved — three named the hosting account, two
needed the Zenodo DOI. The grep above keeps `CHANGEME`, `<DOI` and `<REPOSITORY-URL>` even though
nothing in the release matches them any more, so that a later edit cannot reintroduce one unnoticed.

| File | Placeholder | State |
|---|---|---|
| `CITATION.cff` | `repository-code`, `url` | done — `https://github.com/LuFuqing/compliance-testbed` |
| `NOTICE` | attribution URL | done — the same URL |
| `NOTICE` | `<DOI>` ×1 | done — `10.5281/zenodo.23069546` |
| `README.md` | `<DOI>` ×1 (the BibTeX block) | done — the same DOI |
| `CITATION.cff` | `identifiers:` block | added — the same DOI, with its version/concept roles described |

- [x] **Replace the repository placeholder.** It was `https://github.com/CHANGEME/compliance-testbed`
      in the two `CITATION.cff` fields, plus `<REPOSITORY-URL>` in the `NOTICE` attribution string;
      all three now carry `https://github.com/LuFuqing/compliance-testbed`. Both retired tokens
      still appear in *this* file, inside the illustrative commands and the table above. Those are
      documentation, not metadata, and the scan skips this file.
- [x] **Fill the DOI placeholders** in `NOTICE` and `README.md`, and add an `identifiers:` block to
      `CITATION.cff`. All three carry `10.5281/zenodo.23069546`. The DOI was **reserved on Zenodo
      before the archives were rebuilt**, so the shipped metadata contains its own DOI — a DOI minted
      at publish time can never appear inside the release it identifies. Kept as a checklist item
      because every later version repeats it with that version's own DOI.

### 1c. Decisions only the authors can make

- [ ] **Check the author list and affiliation** in `CITATION.cff`, and the copyright holder in
      `LICENSE` and `NOTICE` (`Lu Fuqing and contributors`). Add co-authors before depositing, not
      after — the DOI record is what people will cite.
- [x] **Decide the licence.** Confirmed by the author on 2026-10-01: **MIT** for code, **CC BY 4.0**
      for data, figures and documentation. Note that the verifier only asserts the two licence files
      *exist* — it never checks *which* licence they contain — so this choice is not enforced by any
      gate. If you change it, edit `LICENSE`, `LICENSE-DATA`, `NOTICE`, `CITATION.cff` (the `license`
      list) and the licence table in `README.md` together so they cannot disagree.
- [ ] **Read `RESULTS.md` §6 and confirm the caveats still apply** to the numbers you are about
      to publish. They are the honest boundary of what the artifact supports.
- [ ] **Update `CHANGELOG.md`** with the version you are depositing and its date. `reproduce.sh`
      reads the release date from the newest entry, so this is the only place the date lives.
- [ ] **Bump `VERSION`** if you are not depositing the current one. It flows into the archive
      names, the verifier banner and `CITATION.cff`'s `version` field automatically.

## 2. Build the archives

```bash
make release          # equivalently: python3 make_release.py
```

This stages the tree into `dist/` as two archives, both wrapped in a single top-level directory
(`compliance_testbed-<version>/`) so that unpacking never scatters files into the user's current
directory:

| Output | Contents |
|---|---|
| `dist/compliance_testbed-1.0.4.zip` | everything: code, results, figures, docs, licences |
| `dist/compliance_testbed-1.0.4.tar.gz` | the same tree, for Unix users |
| `dist/SHA256SUMS` | SHA-256 digests of both archives |

Excluded from the archives: `.git/`, `.venv/`, `venv/`, `dist/`, `build/`, `__pycache__/`,
`*.pyc`, `.DS_Store`, and any pre-existing `*.zip` / `*.tar.gz`.

Archive entry timestamps are pinned to `SOURCE_DATE_EPOCH` (defaulting to the 2026-09-23 release
date), so **rebuilding an unchanged tree yields identical bytes** and the digests are stable —
verified across three consecutive builds. Set `SOURCE_DATE_EPOCH` to override:

```bash
SOURCE_DATE_EPOCH=$(date +%s) python3 make_release.py
```

> **Maintainer note.** Determinism has two independent causes and both must stay fixed.
> For the zip, `ZipInfo.date_time` is pinned. For the `.tar.gz`, resetting `TarInfo.mtime` is
> **not sufficient** — `tarfile.open(mode="w:gz")` writes a gzip header whose MTIME field
> carries the wall-clock time, so the archive differs on every build. `make_release.py`
> therefore builds the tar in memory and compresses it with an explicit `gzip.GzipFile(...,
> mtime=...)`. Do not "simplify" that back to `tarfile.open(out, "w:gz")`; the digest
> stability of the tarball depends on it.

`make_release.py` also self-verifies: it re-reads `SHA256SUMS` immediately after writing it and
fails loudly on any mismatch, so a corrupt build cannot be published unnoticed.

**It also refuses to package a tree whose manifest is stale.** Before staging, it runs
`make_manifest.py --check` and exits non-zero unless `results/SHA256SUMS` describes exactly what
is on disk. This matters because the archive carries whatever is on disk: a manifest left over
from an earlier run would ride in silently, and the package would then ship a manifest that
fails its own check. The order is therefore fixed — **`./reproduce.sh` first, `make release`
second**:

```bash
./reproduce.sh --clean --strict      # rebuilds results/ and rewrites results/SHA256SUMS
make release                         # packages, after checking the manifest
```

Any edit to a tracked file after a reproduction run invalidates the manifest, so re-run
`./reproduce.sh` (or at least `python3 make_manifest.py`) before packaging. To package a
deliberately stale tree, pass `--force`:

```bash
python3 make_release.py --force      # skips the manifest precondition
```

Verify a download against the published sums **from the directory holding the archives**
(`SHA256SUMS` lists bare filenames):

```bash
shasum -a 256 -c SHA256SUMS          # macOS
sha256sum -c SHA256SUMS              # GNU/Linux
```

## 3. Publish to GitHub

`dist/` accumulates one archive pair per released version and is **not** committed (`.gitignore`
excludes it), so nothing stale reaches the repository. It does, however, still sit on disk next to
the current build, and `gh release create` below takes explicit paths — so before uploading,
confirm you are attaching the current version's pair and not an older one:

```bash
ls -1 dist/compliance_testbed-*.zip dist/compliance_testbed-*.tar.gz   # what is actually there
```

Superseded archives can be removed outright; they are reproducible from their own tags:

```bash
rm dist/compliance_testbed-1.0.0.*  dist/compliance_testbed-1.0.1.*  dist/compliance_testbed-1.0.2.*
```

```bash
cd compliance_testbed
git init -b main
git add -A
git commit -m "Compliance-by-design testbed v1.0.4"
git remote add origin git@github.com:<account>/compliance-testbed.git
git push -u origin main
```

Then create a release so the archives are permanently downloadable rather than only rebuildable:

```bash
gh release create v1.0.4 \
  dist/compliance_testbed-1.0.4.zip \
  dist/compliance_testbed-1.0.4.tar.gz \
  dist/SHA256SUMS \
  --title "v1.0.4" \
  --notes-file CHANGELOG.md
```

Tags are the anchor point: cite and link the **tag** (`v1.0.4`), never `main`, because `main`
will move.

> **What goes into the repository and what does not.** `results/` **is** committed — it holds the
> pre-computed numbers a reader audits without running anything, plus `results/SHA256SUMS`.
> `dist/` is **not** committed (`.gitignore` excludes it); the archives belong to the release, not
> to the history, or the repository grows by two archives per release for no benefit.

## 4. Deposit for a citable DOI

GitHub alone gives a URL, not a DOI. Most journals — including Elsevier titles such as Advanced
Engineering Informatics — expect a DOI for a software artifact. There are two routes into Zenodo, and
v1.0.4 used the **manual deposit with a reserved DOI**, because it is the only route that lets the
deposit contain its own DOI:

| Route | What gets archived | Can the deposit contain its own DOI? |
|---|---|---|
| **Manual upload, DOI reserved first** (used for v1.0.4) | the two archives built in §2, plus `dist/SHA256SUMS` | **yes** — Zenodo displays the DOI *before* publication, so it can be written into the files first |
| GitHub ↔ Zenodo integration | GitHub's auto-generated source archive at the tag | **no** — the DOI is minted when the release publishes, and `dist/` is git-ignored, so the built archives are never archived at all |

A DOI becomes immutable once registered, and uploaded files can only be changed within 45 days of
publication (metadata stays editable forever). Hence: get the repository right first, publish last.

### What was done for v1.0.4

1. On Zenodo: *New upload* → answer **No** to "Do you already have a DOI for this upload?" → click
   **Get a DOI now!** The DOI `10.5281/zenodo.23069546` is reserved. **Save the draft** — deleting it
   discards the reserved DOI permanently. A reserved DOI does not resolve until the record is
   published (it answers 404 in the meantime); that is expected, not an error.
2. Write that DOI into the release metadata **before building the archives**:
   - `NOTICE` — the suggested attribution string
   - `README.md` — the BibTeX block
   - `CITATION.cff` — an `identifiers:` block. The `doi:` field is only a shorthand for it, and a
     shorthand cannot distinguish a version DOI from a concept DOI:
     ```yaml
     identifiers:
       - type: doi
         value: 10.5281/zenodo.23069546
         description: "Zenodo DOI for release 1.0.4; also the concept DOI, as this is the first deposit."
     ```
     Cite it as a bare string (`10.5281/…`), never as a resolver URL.
3. Rebuild: `./reproduce.sh --clean --strict` — it must still report `PASS` with **zero** placeholder
   warnings — then `make release`.
4. Commit and push, then create the tag and the GitHub release described in §3.
5. On Zenodo, complete the metadata (resource type *Software*, creators with ORCID, licence, version
   `1.0.4`), upload the two archives plus `dist/SHA256SUMS`, and **Publish**. The DOI now resolves.
6. Once the paper has a DOI of its own, return to the Zenodo record and add it as a related identifier
   `is supplement to`. Never reuse the article's DOI for this deposit — they identify different things.

For later versions, repeat 1–5 with the *new* version DOI, and note that the concept DOI from the
first deposit stays the same — that is the one to keep in `README.md`.

## 5. What the paper's availability statement should claim

Only claim what the artifact actually supports. On the basis of the checks in `reproduce.sh`,
the defensible wording is:

> The testbed, its rule set and all reported results are available at
> `https://doi.org/10.5281/zenodo.23069546`. The artifact contains a one-click reproduction script
> (`./reproduce.sh`) that rebuilds every reported number and figure from scratch and asserts
> them against the values quoted in the accompanying results document (~180 automated checks).
> It also regenerates the supplementary tables it ships — the stress-contrast counts and
> intervals, the sensitivity input/output samples, and the analytic validation of the
> estimators — and a SHA-256 manifest of the released tree. The runs are seeded and
> deterministic; the release was verified end-to-end from a clean checkout. No third-party
> dependencies are required beyond the standard library, and matplotlib for figure rendering
> only.

Because v1.0.4 is the first deposit, its version DOI and the concept DOI are the same number, so
this one link is both "the exact record" and "always the latest". If a later version is deposited
they diverge: keep the concept DOI if the statement should track the newest release, and the version
DOI (`…/zenodo.23069546`) if it must pin the release the paper actually used.

Do **not** claim real-world validation, certification against the cited standards, or
operational deployment. The scenario data are synthetic and the flood-event stress parameters
are expert judgement — see `RESULTS.md` §6.
