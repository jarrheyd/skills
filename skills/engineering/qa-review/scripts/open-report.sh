#!/usr/bin/env bash
# Opens a built report in the human's browser. Kept out of the runner body so a
# run that ends without a visible report is a bug with a test on it, not an
# instruction the agent has to remember.
#
# Usage: open-report.sh <path/to/report.html>
#
# QA_REVIEW_NO_OPEN=1 or CI set: print the path, open nothing.
# QA_REVIEW_OPEN_CMD: use this opener instead of open/xdg-open.
set -euo pipefail

REPORT="${1:-}"
[ -n "$REPORT" ] || { echo "open-report: <report.html> required" >&2; exit 1; }

if [ ! -f "$REPORT" ]; then
  echo "open-report: NOTE no report at $REPORT; the run ended without one" >&2
  exit 0
fi

if [ "${QA_REVIEW_NO_OPEN:-}" = "1" ] || [ -n "${CI:-}" ]; then
  echo "open-report: SKIPPED opening (QA_REVIEW_NO_OPEN=1 or CI). Report: $REPORT"
  exit 0
fi

OPENER="${QA_REVIEW_OPEN_CMD:-}"
if [ -z "$OPENER" ]; then
  if command -v open >/dev/null 2>&1; then
    OPENER="open"
  elif command -v xdg-open >/dev/null 2>&1; then
    OPENER="xdg-open"
  fi
fi

if [ -z "$OPENER" ]; then
  echo "open-report: NOTE no opener on PATH (open, xdg-open). Report: $REPORT"
  exit 0
fi

if $OPENER "$REPORT" >/dev/null 2>&1; then
  echo "open-report: opened $REPORT"
else
  echo "open-report: NOTE $OPENER could not open it. Report: $REPORT" >&2
fi
