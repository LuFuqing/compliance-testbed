#!/usr/bin/env python3
"""Build the distributable archives for the testbed.

  python3 make_release.py            # -> dist/compliance_testbed-<version>.{zip,tar.gz}
  python3 make_release.py --force    # package even if the manifest is stale

Produces two byte-comparable archives, both wrapped in a single top-level
directory so that unpacking never scatters files into the current directory,
plus a SHA256SUMS file for the release. Standard library only, so it runs
anywhere the testbed itself runs.

Before packaging it runs ``make_manifest.py --check``. This is a precondition,
not a convention: the archive carries whatever is on disk, so a
``results/SHA256SUMS`` left over from an earlier run rides in silently and the
package then ships a manifest that fails its own check. Run
``./reproduce.sh`` (or ``python3 make_manifest.py``) first if this refuses.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import os
import sys
import tarfile
import time
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")

# Directories and file patterns never shipped in a release archive.
EXCLUDE_DIRS = {".git", ".venv", "venv", "dist", "build", "__pycache__", ".idea", ".vscode"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db", "LICENSE-DATA.tmp"}
EXCLUDE_SUFFIX = (".pyc", ".pyo", ".zip", ".tar.gz", ".swp")


def version() -> str:
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as fh:
        return fh.read().strip()


def collect(stage_name: str) -> list[tuple[str, str]]:
    """Return [(absolute_path, archive_name)] for everything to ship."""
    items: list[tuple[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for fn in sorted(filenames):
            if fn in EXCLUDE_FILES or fn.endswith(EXCLUDE_SUFFIX):
                continue
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, ROOT)
            items.append((ap, os.path.join(stage_name, rel)))
    return items


def fixed_timestamp() -> float:
    """A stable mtime so repeated builds of the same tree produce identical bytes.

    The default is the release date, 2026-09-23T16:00Z. It must stay a constant:
    deriving it from ``time.time()`` or from the files' own mtimes reintroduces the
    nondeterminism this function exists to remove. Override with SOURCE_DATE_EPOCH.
    """
    return float(os.environ.get("SOURCE_DATE_EPOCH", "1790179200"))


def build_zip(items, out: str, ts: float) -> int:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for ap, name in items:
            zi = zipfile.ZipInfo(name, date_time=time.gmtime(ts)[:6])
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            if os.access(ap, os.X_OK):
                zi.external_attr = 0o755 << 16
            with open(ap, "rb") as fh:
                zf.writestr(zi, fh.read())
    return os.path.getsize(out)


def build_targz(items, out: str, ts: float) -> int:
    """Deterministic .tar.gz.

    Resetting TarInfo.mtime is NOT sufficient: ``tarfile.open(mode="w:gz")`` writes a
    gzip header whose MTIME field carries the current time, so two builds of an
    unchanged tree differ in bytes. The tar stream is therefore built in memory and
    then compressed with an explicit, fixed gzip mtime (and an empty embedded
    filename), which makes the archive byte-identical across builds.
    """
    def reset(ti: tarfile.TarInfo) -> tarfile.TarInfo:
        ti.mtime = int(ts)
        ti.uid = ti.gid = 0
        ti.uname = ti.gname = "root"
        return ti

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for ap, name in items:
            tf.add(ap, arcname=name, filter=reset)

    with open(out, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh,
                           compresslevel=9, mtime=int(ts)) as gz:
            gz.write(buf.getvalue())
    return os.path.getsize(out)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_is_current() -> bool:
    """True when results/SHA256SUMS describes this exact tree."""
    sys.path.insert(0, ROOT)
    import make_manifest  # local module, same directory as this script
    return make_manifest.check() == 0


def main() -> int:
    ver = version()
    stage = f"compliance_testbed-{ver}"
    ts = fixed_timestamp()
    items = collect(stage)

    if not any(n.endswith("verify_results.py") for _, n in items):
        print("ERROR: verify_results.py missing from the tree", file=sys.stderr)
        return 1

    if "--force" not in sys.argv:
        print("precondition: archive manifest describes this tree")
        if not manifest_is_current():
            print("\nERROR: refusing to package -- results/SHA256SUMS is stale.", file=sys.stderr)
            print("       Run ./reproduce.sh (or python3 make_manifest.py) first,",
                  file=sys.stderr)
            print("       or pass --force to package anyway.", file=sys.stderr)
            return 1
        print()
    else:
        print("[--force] skipping the archive-manifest precondition\n")

    os.makedirs(DIST, exist_ok=True)
    zpath = os.path.join(DIST, f"{stage}.zip")
    tpath = os.path.join(DIST, f"{stage}.tar.gz")

    zz = build_zip(items, zpath, ts)
    tz = build_targz(items, tpath, ts)

    raw = sum(os.path.getsize(ap) for ap, _ in items)

    print(f"release {stage}")
    print(f"  files staged : {len(items)}")
    print(f"  raw size     : {raw / 1024:.0f} KB")
    print(f"  {os.path.basename(zpath):<38} {zz / 1024:>7.0f} KB")
    print(f"  {os.path.basename(tpath):<38} {tz / 1024:>7.0f} KB")

    sums = os.path.join(DIST, "SHA256SUMS")
    with open(sums, "w", encoding="utf-8") as fh:
        for p in (zpath, tpath):
            fh.write(f"{sha256(p)}  {os.path.basename(p)}\n")
    print(f"  {os.path.basename(sums):<38} written")

    # Self-verify: SHA256SUMS lists bare filenames, so it is only checkable from the
    # directory holding the archives. Confirm here rather than leaving the user to guess
    # the working directory.
    print("\n  verifying SHA256SUMS:")
    with open(sums, encoding="utf-8") as fh:
        for line in fh:
            digest, name = line.split("  ", 1)
            name = name.strip()
            actual = sha256(os.path.join(DIST, name))
            ok = actual == digest
            print(f"    [{'ok' if ok else 'FAIL'}] {name:<36} {actual}")
            if not ok:
                print("ERROR: digest mismatch immediately after writing", file=sys.stderr)
                return 1
    print("\n  run from the archives' directory:  shasum -a 256 -c SHA256SUMS")
    print("\ncontents:")
    for _, name in items:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
