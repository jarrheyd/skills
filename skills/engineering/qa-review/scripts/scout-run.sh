#!/usr/bin/env bash
# scout suite runner. Runs Maestro flows for one project, on mobile (simulator)
# or web (Chrome), into a fresh run dir under ~/.scout/<project>/runs, then
# builds run-summary.json and report.html and prunes old runs.
#
# Usage:
#   scout-run.sh --repo <path> [--tag smoke] [--flows "a.yaml b.yaml"] [--no-build]
#
# Reads .maestro/scout.config.json in the repo:
#   project, platform (mobile|web), appId|url, buildCmd, installCmd, simulator
# Loads env from ~/.scout/<project>/.env (credentials, injected as maestro -e).
#
# Fail-loud rules: no step swallows its own error; anything bounded or skipped
# is echoed so "passed" never quietly means "did not run".
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="" TAG="" FLOWS="" BUILD_REPORT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2;;
    --tag) TAG="$2"; shift 2;;
    --flows) FLOWS="$2"; shift 2;;
    --no-build) BUILD_REPORT=0; shift;;
    *) echo "scout-run: unknown arg $1" >&2; exit 1;;
  esac
done
[ -n "$REPO" ] || { echo "scout-run: --repo <path> required" >&2; exit 1; }
CONFIG="$REPO/.maestro/scout.config.json"
[ -f "$CONFIG" ] || { echo "scout-run: $CONFIG missing, run scout setup first" >&2; exit 1; }

jqget() { node -e "const c=require('$CONFIG');process.stdout.write(String(c['$1']??''))"; }
PROJECT="$(jqget project)"; PLATFORM="$(jqget platform)"
APP_ID="$(jqget appId)"; URL="$(jqget url)"
BUILD_CMD="$(jqget buildCmd)"; INSTALL_CMD="$(jqget installCmd)"
SIMULATOR="$(jqget simulator)"; SIMULATOR="${SIMULATOR:-iPhone 17}"
[ -n "$PROJECT" ] || { echo "scout-run: config has no project name" >&2; exit 1; }

HOME_DIR="$HOME/.scout/$PROJECT"
RUN_DIR="$HOME_DIR/runs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR/debug"

# Production guard runs before anything launches.
TARGET="${URL:-$APP_ID}"
"$SCRIPT_DIR/guard-env.sh" "$TARGET"

# Credentials: every key in the project .env becomes a maestro -e var. Values
# never echo; set -x stays off.
ENV_ARGS=()
ENV_COUNT=0
if [ -f "$HOME_DIR/.env" ]; then
  while IFS='=' read -r k v; do
    case "$k" in ''|\#*) continue;; esac
    ENV_ARGS+=(-e "$k=$v")
    ENV_COUNT=$((ENV_COUNT + 1))
  done < "$HOME_DIR/.env"
  echo "scout-run: loaded $ENV_COUNT env vars from $HOME_DIR/.env"
else
  echo "scout-run: NOTE no $HOME_DIR/.env found, flows needing credentials will fail"
fi

export PATH="$PATH:$HOME/.maestro/bin"
command -v maestro >/dev/null || { echo "scout-run: maestro not on PATH. Install: curl -fsSL https://get.maestro.mobile.dev | bash" >&2; exit 1; }
# A keg-only Homebrew openjdk is often installed but not on PATH; pick it up.
if ! java -version >/dev/null 2>&1; then
  for jdk in /opt/homebrew/opt/openjdk/bin /usr/local/opt/openjdk/bin; do
    [ -x "$jdk/java" ] && export PATH="$jdk:$PATH" && break
  done
fi
if ! java -version >/dev/null 2>&1; then
  echo "scout-run: no Java runtime; Maestro cannot start. Fix: brew install --cask temurin" >&2
  exit 1
fi

DEVICE_ARGS=()
if [ "$PLATFORM" = "android" ]; then
  # Android: best-effort. Needs a running emulator or connected device (adb devices).
  command -v adb >/dev/null || { echo "scout-run: adb not on PATH; install Android platform-tools" >&2; exit 1; }
  SERIAL="$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')"
  [ -n "$SERIAL" ] || { echo "scout-run: no Android device or emulator online (adb devices). Start one and rerun." >&2; exit 1; }
  DEVICE_ARGS=(--device "$SERIAL")
  if [ -n "$BUILD_CMD" ] && [ "${SCOUT_SKIP_BUILD:-}" != "1" ]; then
    echo "scout-run: building app ($BUILD_CMD). Set SCOUT_SKIP_BUILD=1 to reuse the installed build."
    (cd "$REPO" && eval "$BUILD_CMD")
  else
    echo "scout-run: SKIPPED build step (SCOUT_SKIP_BUILD=1 or no buildCmd); testing the already-installed binary"
  fi
  if [ -n "$INSTALL_CMD" ] && [ "${SCOUT_SKIP_BUILD:-}" != "1" ]; then
    (cd "$REPO" && eval "$INSTALL_CMD")
  fi
elif [ "$PLATFORM" = "mobile" ]; then
  # Prefer a booted simulator matching the configured name; else any booted one; else boot the named one.
  UDID="$(xcrun simctl list devices booted | grep -m1 "$SIMULATOR (" | grep -oE '[0-9A-F-]{36}' || true)"
  if [ -z "$UDID" ]; then
    BOOTED="$(xcrun simctl list devices booted | grep -m1 -oE '[0-9A-F-]{36}' || true)"
    if [ -n "$BOOTED" ]; then
      echo "scout-run: NOTE using the already-booted simulator $BOOTED, not \"$SIMULATOR\" from scout.config.json"
      UDID="$BOOTED"
    fi
  fi
  if [ -z "$UDID" ]; then
    UDID="$(xcrun simctl list devices available | grep -m1 "$SIMULATOR (" | grep -oE '[0-9A-F-]{36}' || true)"
    [ -n "$UDID" ] || { echo "scout-run: simulator \"$SIMULATOR\" not found" >&2; exit 1; }
    xcrun simctl boot "$UDID"
    xcrun simctl bootstatus "$UDID" -b
  fi
  DEVICE_ARGS=(--device "$UDID")
  if [ -n "$BUILD_CMD" ] && [ "${SCOUT_SKIP_BUILD:-}" != "1" ]; then
    echo "scout-run: building app ($BUILD_CMD). Set SCOUT_SKIP_BUILD=1 to reuse the installed build."
    (cd "$REPO" && eval "$BUILD_CMD")
  else
    echo "scout-run: SKIPPED build step (SCOUT_SKIP_BUILD=1 or no buildCmd); testing the already-installed binary"
  fi
  if [ -n "$INSTALL_CMD" ] && [ "${SCOUT_SKIP_BUILD:-}" != "1" ]; then
    (cd "$REPO" && eval "$INSTALL_CMD")
  fi
else
  # Web: Maestro drives its own Chromium. The flows carry url: themselves;
  # nothing to boot here.
  echo "scout-run: web platform, flows drive Chrome directly"
fi

# Flow selection in bash (mirrors the production suites): glob flows/*.yaml,
# skip _partials, keep everything or only files whose tag block contains TAG.
cd "$REPO/.maestro"
SELECTED=()
if [ -n "$FLOWS" ]; then
  for f in $FLOWS; do SELECTED+=("flows/$(basename "$f")"); done
else
  for f in flows/*.yaml; do
    base="$(basename "$f")"
    case "$base" in _*) continue;; esac
    if [ -n "$TAG" ]; then
      grep -qE "^  - $TAG\$" "$f" || continue
    fi
    SELECTED+=("$f")
  done
fi
[ ${#SELECTED[@]} -gt 0 ] || { echo "scout-run: no flows selected (tag=$TAG)" >&2; exit 1; }

# Web flows carry their own url: header, so guard every selected flow's target too,
# not only the config value.
for f in "${SELECTED[@]}"; do
  for u in $(grep -hoE '^\s*(url|-\s*openLink):\s*\S+' "$f" | awk '{print $NF}' | tr -d '"'"'"'"'); do
    "$SCRIPT_DIR/guard-env.sh" "$u" >/dev/null
  done
done
echo "scout-run: running ${#SELECTED[@]} flow(s): ${SELECTED[*]}"

# One invocation for the set; per-flow retry for failures. A wedged driver call
# can hang, so everything runs under a hard timeout.
RESULT="$RUN_DIR/result.xml"
TIMEOUT_BIN="$(command -v timeout || command -v gtimeout || true)"
run_maestro() { # args: junit-out, flows...
  local out="$1"; shift
  # macOS ships bash 3.2, where expanding an empty array under set -u errors;
  # the ${arr[@]+...} form is the portable guard.
  local cmd=(maestro ${DEVICE_ARGS[@]+"${DEVICE_ARGS[@]}"} test "$@" ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} --format junit --output "$out" --debug-output "$RUN_DIR/debug")
  if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" "${SCOUT_SUITE_TIMEOUT:-3600}" "${cmd[@]}"; else "${cmd[@]}"; fi
}
# Portable per-flow timeout: macOS has no `timeout`; perl's alarm does the job.
with_timeout() { # secs, cmd...
  local secs="$1"; shift
  if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" "$secs" "$@"; else perl -e 'alarm shift; exec @ARGV' "$secs" "$@"; fi
}
run_flow() { # args: junit-out, flow
  local out="$1" flow="$2"
  with_timeout "${SCOUT_FLOW_TIMEOUT:-900}" maestro ${DEVICE_ARGS[@]+"${DEVICE_ARGS[@]}"} test "$flow" ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} --format junit --output "$out" --debug-output "$RUN_DIR/debug"
}
# Per-flow mode: one maestro invocation per flow. Maestro validates the whole
# workspace before a multi-flow run and aborts everything on a single addMedia
# path it cannot resolve (0 flows executed); per-flow runs are immune and also
# isolate a wedged driver to one flow. Default on; SCOUT_PER_FLOW=0 for the
# single-invocation mode.
PER_FLOW="${SCOUT_PER_FLOW:-1}"
set +e
if [ "$PER_FLOW" = "1" ]; then
  SUITE_RC=0
  FAILED_LIST=""
  for f in "${SELECTED[@]}"; do
    name="$(basename "${f%.yaml}")"
    echo "scout-run: [$name] running"
    run_flow "$RUN_DIR/result-$name.xml" "$f"
    rc=$?
    if [ $rc -ne 0 ]; then SUITE_RC=1; FAILED_LIST="$FAILED_LIST $name"; echo "scout-run: [$name] FAILED (rc=$rc)"; else echo "scout-run: [$name] passed"; fi
  done
  if [ -n "$FAILED_LIST" ] && [ "${SCOUT_NO_RETRY:-}" != "1" ]; then
    echo "scout-run: retrying failed flows once:$FAILED_LIST"
    for name in $FAILED_LIST; do
      run_flow "$RUN_DIR/result-retry-$name.xml" "flows/$name.yaml" && echo "scout-run: [$name] passed on retry" || echo "scout-run: [$name] failed again"
    done
  fi
else
  run_maestro "$RESULT" "${SELECTED[@]}"
  SUITE_RC=$?
fi
set -e

if [ "$PER_FLOW" != "1" ] && [ $SUITE_RC -ne 0 ] && [ "${SCOUT_NO_RETRY:-}" != "1" ]; then
  echo "scout-run: suite had failures (rc=$SUITE_RC), retrying failed flows once"
  FAILED=$(node -e "
    const fs=require('fs');
    const xml=fs.existsSync('$RESULT')?fs.readFileSync('$RESULT','utf8'):'';
    const bad=[...xml.matchAll(/<testcase\b[^>]*name=\"([^\"]+)\"[^>]*>([\s\S]*?)<\/testcase>/g)]
      .filter(m=>/<failure|<error/.test(m[2])).map(m=>m[1]);
    process.stdout.write(bad.join(' '));
  ")
  if [ -n "$FAILED" ]; then
    for flow in $FAILED; do
      set +e
      run_maestro "$RUN_DIR/result-retry-${flow%.yaml}.xml" "flows/${flow%.yaml}.yaml"
      set -e
    done
  fi
fi

node "$SCRIPT_DIR/summarize-run.mjs" --run "$RUN_DIR"

if [ "$BUILD_REPORT" = "1" ]; then
  JUNITS="$(ls "$RUN_DIR"/result*.xml 2>/dev/null | tr '\n' ',' | sed 's/,$//')"
  PREV="$(ls -t "$HOME_DIR"/runs/*/report.html 2>/dev/null | sed -n 2p || true)"
  node "$SCRIPT_DIR/build-report.mjs" \
    --project "$PROJECT" \
    --manifest "$REPO/.maestro/journeys.manifest.json" \
    --config "$CONFIG" \
    --debug "$RUN_DIR/debug" \
    --junit "$JUNITS" \
    --out "$RUN_DIR/report.html" \
    --build "run $(date +%Y-%m-%d\ %H:%M)" \
    ${PREV:+--previous "$PREV"}
fi

node "$SCRIPT_DIR/prune-runs.mjs" --project "$PROJECT" --keep "${SCOUT_KEEP_RUNS:-2}"
echo "scout-run: done. Summary: $RUN_DIR/run-summary.json Report: $RUN_DIR/report.html"
