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

As of v1.0.4 there were five, in three groups. The three that name the hosting account are now
resolved; the two that need the DOI are not. The grep above keeps the `CHANGEME` and
`<REPOSITORY-URL>` patterns even though nothing matches them any more, so that a later edit cannot
reintroduce one unnoticed.

| File | Placeholder | State |
|---|---|---|
| `CITATION.cff` | `repository-code`, `url` | done — `https://github.com/LuFuqing/compliance-testbed` |
| `NOTICE` | attribution URL | done — the same URL |
| `NOTICE` | `<DOI>` ×1 | **open** — the Zenodo DOI once deposited (§4) |
| `README.md` | `<DOI>` ×1 (the BibTeX block) | **open** — the same DOI |

- [x] **Replace the repository placeholder.** It was `https://github.com/CHANGEME/compliance-testbed`
      in the two `CITATION.cff` fields, plus `<REPOSITORY-URL>` in the `NOTICE` attribution string;
      all three now carry `https://github.com/LuFuqing/compliance-testbed`. Both retired tokens
      still appear in *this* file, inside the illustrative commands and the table above. Those are
      documentation, not metadata, and the scan skips this file.
- [ ] **Fill the DOI placeholders** in `NOTICE` and `README.md` after depositing (§4), and add an
      `identifiers:` block to `CITATION.cff` at the same time. A bare `<DOI>` inside an
      attribution string is the one placeholder that ends up in somebody's citation.

### 1c. Decisions only the authors can make

- [ ] **Check the author list and affiliation** in `CITATION.cff`, and the copyright holder in
      `LICENSE` and `NOTICE` (`Lu Fuqing and contributors`). Add co-authors before depositing, not
      after — the DOI record is what people will cite.
- [ ] **Decide the licence.** The shipped split is MIT for code and CC BY 4.0 for data/figures.
      This is the recommended default for journal artifacts, but it is a decision for the authors.
      If you change it, edit `LICENSE`, `LICENSE-DATA`, `NOTICE`, `CITATION.cff` (the `license`
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
Engineering Informatics — expect a DOI for a software artifact, so deposit through Zenodo, which
integrates directly with GitHub releases:

1. Sign in to [zenodo.org](https://zenodo.org) with GitHub and authorise the repository under
   *Settings → GitHub*.
2. Return to GitHub, edit the release you just created, and press **Publish** if the Zenodo
   webhook has not already minted a DOI. Zenodo reserves a DOI for every release.
3. Copy the **concept DOI** (the one that always resolves to the latest version) for the paper's
   Data/Code Availability statement, and the **version DOI** for the exact v1.0.4 record.
4. Update every place that references the DOI:
   - `CITATION.cff` — add an `identifiers:` block:
     ```yaml
     identifiers:
       - type: doi
         value: 10.5281/zenodo.XXXXXXX
         description: "Version 1.0.4"
     ```
   - `NOTICE` — replace the `<DOI>` placeholder in the suggested attribution string.
   - `README.md` — replace the `<DOI>` placeholder in the BibTeX block.
5. Commit, and mint a new patch release (e.g. `v1.0.4a`) if you want the corrected metadata
   reflected in the archived record. The version DOI for the original deposit stays valid and
   immutable, which is exactly what a citation needs.

## 5. What the paper's availability statement should claim

Only claim what the artifact actually supports. On the basis of the checks in `reproduce.sh`,
the defensible wording is:

> The testbed, its rule set and all reported results are available at
> `https://doi.org/<concept-DOI>`. The artifact contains a one-click reproduction script
> (`./reproduce.sh`) that rebuilds every reported number and figure from scratch and asserts
> them against the values quoted in the accompanying results document (~180 automated checks).
> It also regenerates the supplementary tables it ships — the stress-contrast counts and
> intervals, the sensitivity input/output samples, and the analytic validation of the
> estimators — and a SHA-256 manifest of the released tree. The runs are seeded and
> deterministic; the release was verified end-to-end from a clean checkout. No third-party
> dependencies are required beyond the standard library, and matplotlib for figure rendering
> only.

Do **not** claim real-world validation, certification against the cited standards, or
operational deployment. The scenario data are synthetic and the flood-event stress parameters
are expert judgement — see `RESULTS.md` §6.
