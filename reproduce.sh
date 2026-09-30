#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# One-click reproduction of the compliance-by-design testbed.
# The artifact version and release date are read from VERSION and CHANGELOG.md,
# so this file never carries a stale version stamp of its own.
#
#   ./reproduce.sh                 full run: scenario suite + stress/sensitivity + supplementary + figures + verification
#   ./reproduce.sh --strict        make release-fingerprint drift a failure
#   ./reproduce.sh --no-figures    skip figure generation (no matplotlib needed)
#   ./reproduce.sh --clean         delete results/ first, then rebuild from zero
#   ./reproduce.sh --install-deps  create ./.venv and pip install matplotlib
#   ./reproduce.sh --python /path/to/python
#
# Exit code 0 = the reported numbers were reproduced and verified.
# ---------------------------------------------------------------------------
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1

STRICT=""
NO_FIGURES=""
CLEAN=""
INSTALL_DEPS=""
PY="${PYTHON:-}"

while [ $# -gt 0 ]; do
    case "$1" in
        --strict)       STRICT="--strict" ;;
        --no-figures)   NO_FIGURES="1" ;;
        --clean)        CLEAN="1" ;;
        --install-deps) INSTALL_DEPS="1" ;;
        --python)       shift; PY="${1:-}" ;;
        -h|--help)      awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "unknown option: $1  (try --help)" >&2; exit 2 ;;
    esac
    shift
done

banner() { printf '\n%s\n%s\n' "$1" "$(printf '=%.0s' $(seq 1 ${#1}))"; }
ok()     { printf '  \033[32m[ok]\033[0m   %s\n' "$1"; }
warn()   { printf '  \033[33m[warn]\033[0m %s\n' "$1"; }
fail()   { printf '  \033[31m[FAIL]\033[0m %s\n' "$1"; }

START=$(date +%s)

banner "Compliance-by-Design Testbed - one-click reproduction"
VERSION_STR="$(cat VERSION 2>/dev/null || echo unknown)"
# Date comes from the newest CHANGELOG entry, so VERSION and the release date have
# exactly one source each and cannot drift apart.  The newest header looks like
#   ## [1.0.4] - 2026-09-23      (the separator may be an em dash)
RELEASE_DATE="$(awk '/^## \[/{print $NF; exit}' CHANGELOG.md 2>/dev/null)"
case "$RELEASE_DATE" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
    *) RELEASE_DATE="unknown" ;;
esac
echo "  artifact : $VERSION_STR  (released ${RELEASE_DATE})"
echo "  root     : $ROOT"

# ---------------------------------------------------------------- 0. dependencies
if [ "$INSTALL_DEPS" = "1" ]; then
    banner "Installing dependencies into ./.venv"
    if [ -z "$PY" ]; then
        PY="$(command -v python3 || true)"
    fi
    if [ -z "$PY" ]; then
        fail "no python3 on PATH to bootstrap a virtual environment"
        exit 1
    fi
    "$PY" -m venv "$ROOT/.venv" || { fail "venv creation failed"; exit 1; }
    PY="$ROOT/.venv/bin/python"
    "$PY" -m pip install --quiet --upgrade pip
    "$PY" -m pip install --quiet matplotlib || { fail "pip install matplotlib failed"; exit 1; }
    ok "virtual environment ready at ./.venv"
fi

# ---------------------------------------------------------------- 1. interpreter
banner "1/6  Interpreter"
if [ -z "$PY" ]; then
    for cand in python3 python3.13 python3.12 python3.11 python3.10 python3.9 python; do
        if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
    done
fi
if [ -z "$PY" ]; then
    fail "no Python interpreter found. Install Python 3.9+ or pass --python /path/to/python"
    exit 1
fi

PYVER="$("$PY" -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])' 2>/dev/null)"
PYMAJ="$("$PY" -c 'import sys;print(sys.version_info[0])' 2>/dev/null)"
PYMIN="$("$PY" -c 'import sys;print(sys.version_info[1])' 2>/dev/null)"
if [ "$PYMAJ" -lt 3 ] || { [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 9 ]; }; then
    fail "Python $PYVER is too old; 3.9+ required"
    exit 1
fi
ok "python: $("$PY" -c 'import sys;print(sys.executable)')  (version $PYVER)"

HAVE_MPL=0
if "$PY" -c 'import matplotlib' >/dev/null 2>&1; then
    MPLVER="$("$PY" -c 'import matplotlib;print(matplotlib.__version__)' 2>/dev/null)"
    HAVE_MPL=1
    ok "matplotlib $MPLVER present - figures will be regenerated"
else
    warn "matplotlib absent - figures 1-4 cannot be regenerated"
    warn "for a FULL reproduction run:  ./reproduce.sh --install-deps"
fi

# GEN_FIG decides whether figures are produced AND validated in this run
GEN_FIG=1
if [ "$HAVE_MPL" -eq 0 ] || [ -n "$NO_FIGURES" ]; then
    GEN_FIG=0
fi
if [ -n "$NO_FIGURES" ] && [ "$HAVE_MPL" -eq 1 ]; then
    warn "--no-figures given: figures will neither be regenerated nor validated"
fi

# ---------------------------------------------------------------- 2. clean
banner "2/6  Workspace"
if [ "$CLEAN" = "1" ]; then
    rm -rf "$ROOT/results"
    ok "removed results/ (rebuilding from zero)"
else
    ok "results/ left in place (use --clean for a from-zero rebuild)"
fi
mkdir -p "$ROOT/results/figures"
ok "results/ and results/figures/ exist"

# ------------------------------------------------------------ 3. scenario suite
banner "3/6  Scenario suite - scenario comparison + Morris screening (standard library only)"
SCEN_START=$(date +%s)
if ! "$PY" run_all.py; then
    fail "scenario suite failed"
    exit 1
fi
ok "scenario suite complete in $(( $(date +%s) - SCEN_START ))s"

# --------------------------------------- 4. stress and sensitivity + supplementary
banner "4/6  Stress and sensitivity - SL/T 853-855 contrast + Sobol + supplementary tables"
STRESS_START=$(date +%s)
STRESS_ARGS=""
[ "$GEN_FIG" -eq 0 ] && STRESS_ARGS="--no-figures"
if ! "$PY" run_stress_sensitivity.py $STRESS_ARGS; then
    fail "stress and sensitivity suite failed"
    exit 1
fi
ok "stress and sensitivity complete in $(( $(date +%s) - STRESS_START ))s"

# ---------------------------------------------------------------- 5. manifest
banner "5/6  Archive manifest (SHA-256)"
if ! "$PY" make_manifest.py; then
    fail "manifest generation failed"
    exit 1
fi
ok "results/SHA256SUMS written"

# ---------------------------------------------------------------- 6. verify
banner "6/6  Golden-value verification"
VSKIP=""
if [ "$GEN_FIG" -eq 0 ]; then
    VSKIP="--skip-figures"
fi
if "$PY" verify_results.py $STRICT $VSKIP; then
    VRC=0
else
    VRC=$?
fi

TOTAL=$(( $(date +%s) - START ))
printf '\n%s\n' "$(printf '=%.0s' $(seq 1 78))"
if [ "$VRC" -eq 0 ]; then
    if [ "$GEN_FIG" -eq 1 ]; then
        printf 'REPRODUCTION: SUCCESS in %ss\n' "$TOTAL"
        echo "All reported numbers and figures in results/ were rebuilt and verified."
    else
        printf 'REPRODUCTION: PARTIAL in %ss (figures not regenerated)\n' "$TOTAL"
        echo "All reported NUMBERS were rebuilt and verified, but figures 1-4 were not,"
        echo "because matplotlib is unavailable. Re-run with --install-deps for a full run."
    fi
    echo "Interpretation of the results: RESULTS.md"
    echo "Supplementary tables: results/stress_contrast.csv, results/sobol_samples.csv,"
    echo "                      results/estimator_validation.csv"
    echo "Archive manifest:     results/SHA256SUMS  (verify with: python3 make_manifest.py --check)"
    exit 0
else
    printf 'REPRODUCTION: FAILED in %ss - see the failing checks above\n' "$TOTAL"
    exit 1
fi
