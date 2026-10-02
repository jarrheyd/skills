#!/usr/bin/env bash
# qa-review regression, the repeatable one-command full pass.
#
#   qa-review-regression.sh --repo <path> [--max-resumes 3] [--resume]
#   --resume continues the newest run dir (no rebuild, no reseed) instead of starting fresh.
#
# 1. Freshness: flags selectors with no match in the current code (gaps.json).
# 2. Full run via qa-review-run.sh: build, install, seed (config seedCmd), every flow.
# 3. Resume: while any flow has no result (a wedge, a crash, a killed driver),
#    re-invoke with --resume so the suite finishes instead of restarting.
# 4. The runner retries each red flow once on its own, so a one-off driver blip
#    does not read as a defect (both attempts stay in the run dir).
# 5. UI review set: every captured screen downscaled into <run>/ui-review for the
#    UI and consistency pass (the agent reviews it; see modes/regression.md).
# Prints the run dir on the last line.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="" MAX_RESUMES=3 CONTINUE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2;;
    --max-resumes) MAX_RESUMES="$2"; shift 2;;
    --resume) CONTINUE=1; shift;;
    *) echo "qa-review-regression: unknown arg $1" >&2; exit 1;;
  esac
done
[ -n "$REPO" ] || { echo "qa-review-regression: --repo <path> required" >&2; exit 1; }
REPO="$(cd "$REPO" && pwd)"
CONFIG="${QA_REVIEW_CONFIG:-$REPO/.maestro/qa-review.config.json}"
[ -n "${QA_REVIEW_CONFIG:-}" ] || [ -f "$CONFIG" ] || CONFIG="$REPO/qa-review.config.json"
case "$CONFIG" in /*) ;; *) CONFIG="$REPO/$CONFIG";; esac
export QA_REVIEW_CONFIG="$CONFIG"
PROJECT="$(node -e "process.stdout.write(require('$CONFIG').project)")"
RUNNER="$(node -e "process.stdout.write(require('$CONFIG').runner||'maestro')")"
HOME_DIR="$HOME/.qa-review/$PROJECT"

# The suite: Maestro flow files, or for the Playwright runner every journey in
# the manifest that is not marked planned.
suite() {
  if [ "$RUNNER" = "playwright" ]; then
    node -e "const m=require('$(dirname "$CONFIG")/journeys.manifest.json');process.stdout.write((m.journeys||[]).filter(j=>!j.planned).map(j=>j.flow).join('\n'))"
  else
    node "$SCRIPT_DIR/config-glob.mjs" "$CONFIG" suite "$REPO/.maestro/flows"
  fi
}

if [ "$RUNNER" = "playwright" ]; then
  echo "== freshness: skipped (a Playwright spec fails on a stale selector by itself)"
  # A Playwright run does not wedge half-way like a device driver, so there is
  # nothing to resume: a spec with no result did not run, and that is reported.
  MAX_RESUMES=0
else
  echo "== freshness"
  node "$SCRIPT_DIR/check-flow-freshness.mjs" --repo "$REPO" || true
fi

if [ "$CONTINUE" = "1" ]; then
  echo "== continuing the newest run"
  QA_REVIEW_PER_FLOW=1 QA_REVIEW_NO_OPEN=1 QA_REVIEW_SKIP_BUILD=1 "$SCRIPT_DIR/qa-review-run.sh" --repo "$REPO" --resume || true
else
  echo "== full run"
  QA_REVIEW_PER_FLOW=1 QA_REVIEW_NO_OPEN=1 "$SCRIPT_DIR/qa-review-run.sh" --repo "$REPO" || true
fi
RUN_DIR="$(ls -dt "$HOME_DIR"/runs/*/ | head -1)"; RUN_DIR="${RUN_DIR%/}"

missing() {
  local n=0
  while read -r f; do
    [ -z "$f" ] && continue
    [ -f "$RUN_DIR/result-${f%.yaml}.xml" ] || [ -f "$RUN_DIR/result-retry-${f%.yaml}.xml" ] || n=$((n+1))
  done < <(suite; echo)
  echo "$n"
}
[ "$MAX_RESUMES" -gt 0 ] && for i in $(seq 1 "$MAX_RESUMES"); do
  m="$(missing)"
  [ "$m" = "0" ] && break
  echo "== resume $i: $m flow(s) without a result"
  QA_REVIEW_PER_FLOW=1 QA_REVIEW_NO_OPEN=1 QA_REVIEW_SKIP_BUILD=1 "$SCRIPT_DIR/qa-review-run.sh" --repo "$REPO" --resume || true
done
echo "== flows still without a result: $(missing)"

echo "== UI review set"
node "$SCRIPT_DIR/ui-gallery.mjs" --run "$RUN_DIR"

echo "== result"
pass=0; fail=0; failed=""
while read -r f; do
  [ -z "$f" ] && continue
  n="${f%.yaml}"; x="$RUN_DIR/result-$n.xml"; r="$RUN_DIR/result-retry-$n.xml"
  if [ -f "$r" ] && ! grep -q "<failure\|<error" "$r"; then pass=$((pass+1))
  elif [ -f "$x" ] && ! grep -q "<failure\|<error" "$x"; then pass=$((pass+1))
  elif [ -f "$x" ] || [ -f "$r" ]; then fail=$((fail+1)); failed="$failed $n"
  fi
done < <(suite; echo)
echo "passed: $pass  failed: $fail  without a result: $(missing)"
[ -n "$failed" ] && echo "failed:$failed"
echo "next: classify each red, repair stale flows, run the UI pass, publish (modes/regression.md)"
echo "$RUN_DIR"
