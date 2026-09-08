#!/usr/bin/env bash
# qa-review suite runner. Runs Maestro flows for one project, on mobile (simulator)
# or web (Chrome), into a fresh run dir under ~/.qa-review/<project>/runs, then
# builds run-summary.json and report.html and prunes old runs.
#
# Usage:
#   qa-review-run.sh --repo <path> [--tag smoke] [--flows "a.yaml b.yaml"] [--no-build]
#
# Reads .maestro/qa-review.config.json in the repo:
#   project, platform (mobile|web), appId|url, buildCmd, installCmd, simulator
# Loads env from ~/.qa-review/<project>/.env (credentials, injected as maestro -e).
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
    *) echo "qa-review: unknown arg $1" >&2; exit 1;;
  esac
done
[ -n "$REPO" ] || { echo "qa-review: --repo <path> required" >&2; exit 1; }
CONFIG="$REPO/.maestro/qa-review.config.json"
[ -f "$CONFIG" ] || { echo "qa-review: $CONFIG missing, run qa-review setup first" >&2; exit 1; }

jqget() { node -e "const c=require('$CONFIG');process.stdout.write(String(c['$1']??''))"; }
PROJECT="$(jqget project)"; PLATFORM="$(jqget platform)"
APP_ID="$(jqget appId)"; URL="$(jqget url)"
BUILD_CMD="$(jqget buildCmd)"; INSTALL_CMD="$(jqget installCmd)"
SIMULATOR="$(jqget simulator)"; SIMULATOR="${SIMULATOR:-iPhone 17}"
[ -n "$PROJECT" ] || { echo "qa-review: config has no project name" >&2; exit 1; }

HOME_DIR="$HOME/.qa-review/$PROJECT"
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
  echo "qa-review: loaded $ENV_COUNT env vars from $HOME_DIR/.env"
else
  echo "qa-review: NOTE no $HOME_DIR/.env found, flows needing credentials will fail"
fi

export PATH="$PATH:$HOME/.maestro/bin"
command -v maestro >/dev/null || { echo "qa-review: maestro not on PATH. Install: curl -fsSL https://get.maestro.mobile.dev | bash" >&2; exit 1; }
# A keg-only Homebrew openjdk is often installed but not on PATH; pick it up.
if ! java -version >/dev/null 2>&1; then
  for jdk in /opt/homebrew/opt/openjdk/bin /usr/local/opt/openjdk/bin; do
    [ -x "$jdk/java" ] && export PATH="$jdk:$PATH" && break
  done
fi
if ! java -version >/dev/null 2>&1; then
  echo "qa-review: no Java runtime; Maestro cannot start. Fix: brew install --cask temurin" >&2
  exit 1
fi

DEVICE_ARGS=()
if [ "$PLATFORM" = "android" ]; then
  # Android: best-effort. Needs a running emulator or connected device (adb devices).
  command -v adb >/dev/null || { echo "qa-review: adb not on PATH; install Android platform-tools" >&2; exit 1; }
  SERIAL="$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')"
  [ -n "$SERIAL" ] || { echo "qa-review: no Android device or emulator online (adb devices). Start one and rerun." >&2; exit 1; }
  DEVICE_ARGS=(--device "$SERIAL")
  if [ -n "$BUILD_CMD" ] && [ "${QA_REVIEW_SKIP_BUILD:-}" != "1" ]; then
    echo "qa-review: building app ($BUILD_CMD). Set QA_REVIEW_SKIP_BUILD=1 to reuse the installed build."
    (cd "$REPO" && eval "$BUILD_CMD")
  else
    echo "qa-review: SKIPPED build step (QA_REVIEW_SKIP_BUILD=1 or no buildCmd); testing the already-installed binary"
  fi
  if [ -n "$INSTALL_CMD" ] && [ "${QA_REVIEW_SKIP_BUILD:-}" != "1" ]; then
    (cd "$REPO" && eval "$INSTALL_CMD")
  fi
elif [ "$PLATFORM" = "mobile" ]; then
  # Prefer a booted simulator matching the configured name; else any booted one; else boot the named one.
  UDID="$(xcrun simctl list devices booted | grep -m1 "$SIMULATOR (" | grep -oE '[0-9A-F-]{36}' || true)"
  if [ -z "$UDID" ]; then
    BOOTED="$(xcrun simctl list devices booted | grep -m1 -oE '[0-9A-F-]{36}' || true)"
    if [ -n "$BOOTED" ]; then
      echo "qa-review: NOTE using the already-booted simulator $BOOTED, not \"$SIMULATOR\" from qa-review.config.json"
      UDID="$BOOTED"
    fi
  fi
  if [ -z "$UDID" ]; then
    UDID="$(xcrun simctl list devices available | grep -m1 "$SIMULATOR (" | grep -oE '[0-9A-F-]{36}' || true)"
    [ -n "$UDID" ] || { echo "qa-review: simulator \"$SIMULATOR\" not found" >&2; exit 1; }
    xcrun simctl boot "$UDID"
    xcrun simctl bootstatus "$UDID" -b
  fi
  DEVICE_ARGS=(--device "$UDID")
  if [ -n "$BUILD_CMD" ] && [ "${QA_REVIEW_SKIP_BUILD:-}" != "1" ]; then
    echo "qa-review: building app ($BUILD_CMD). Set QA_REVIEW_SKIP_BUILD=1 to reuse the installed build."
    (cd "$REPO" && eval "$BUILD_CMD")
  else
    echo "qa-review: SKIPPED build step (QA_REVIEW_SKIP_BUILD=1 or no buildCmd); testing the already-installed binary"
  fi
  if [ -n "$INSTALL_CMD" ] && [ "${QA_REVIEW_SKIP_BUILD:-}" != "1" ]; then
    (cd "$REPO" && eval "$INSTALL_CMD")
  fi
else
  # Web: Maestro drives its own Chromium. The flows carry url: themselves;
  # nothing to boot here.
  echo "qa-review: web platform, flows drive Chrome directly"
fi

# Build fingerprint: what was actually under test, so a later report can tell
# whether evidence it carried forward still describes this build. The installed
# binary is the honest answer on device: under QA_REVIEW_SKIP_BUILD=1 the commit
# moves while the binary does not, and a sideloaded build changes the binary
# while the commit does not. Web has no binary, so the commit is all there is.
# No fingerprint means carried evidence expires rather than counting green.
build_fingerprint() {
  case "$PLATFORM" in
    mobile)
      local container exe
      container="$(xcrun simctl get_app_container "$UDID" "$APP_ID" app 2>/dev/null || true)"
      [ -n "$container" ] && [ -d "$container" ] || return 0
      exe="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$container/Info.plist" 2>/dev/null || true)"
      [ -n "$exe" ] && [ -f "$container/$exe" ] || return 0
      printf 'binary %s' "$(shasum -a 256 "$container/$exe" | awk '{print $1}')"
      ;;
    android)
      local apk
      apk="$(adb -s "$SERIAL" shell pm path "$APP_ID" 2>/dev/null | head -1 | sed 's/^package://' | tr -d '\r')"
      [ -n "$apk" ] || return 0
      printf 'binary %s' "$(adb -s "$SERIAL" shell md5sum "$apk" 2>/dev/null | awk '{print $1}' | tr -d '\r')"
      ;;
    *)
      local sha dirty
      sha="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || true)"
      [ -n "$sha" ] || return 0
      dirty=""
      git -C "$REPO" diff --quiet 2>/dev/null || dirty="-dirty"
      printf 'commit %s%s' "$sha" "$dirty"
      ;;
  esac
}
FINGERPRINT="$(build_fingerprint || true)"
if [ -n "$FINGERPRINT" ]; then
  node -e "
    const fs=require('fs');
    const [kind,...rest]=process.argv[1].split(' ');
    fs.writeFileSync('$RUN_DIR/build.json', JSON.stringify({kind,hash:rest.join(' '),at:new Date().toISOString()},null,2)+'\n');
  " "$FINGERPRINT"
  echo "qa-review: build fingerprint ${FINGERPRINT%% *} ${FINGERPRINT##* }"
else
  echo "qa-review: NOTE no build fingerprint for platform $PLATFORM; carried evidence will expire instead of counting green"
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
[ ${#SELECTED[@]} -gt 0 ] || { echo "qa-review: no flows selected (tag=$TAG)" >&2; exit 1; }

# Web flows carry their own url: header, so guard every selected flow's target too,
# not only the config value.
for f in "${SELECTED[@]}"; do
  for u in $(grep -hoE '^\s*(url|-\s*openLink):\s*\S+' "$f" | awk '{print $NF}' | tr -d '"'"'"'"'); do
    "$SCRIPT_DIR/guard-env.sh" "$u" >/dev/null
  done
done
echo "qa-review: running ${#SELECTED[@]} flow(s): ${SELECTED[*]}"

# One invocation for the set; per-flow retry for failures. A wedged driver call
# can hang, so everything runs under a hard timeout.
RESULT="$RUN_DIR/result.xml"
TIMEOUT_BIN="$(command -v timeout || command -v gtimeout || true)"
run_maestro() { # args: junit-out, flows...
  local out="$1"; shift
  # macOS ships bash 3.2, where expanding an empty array under set -u errors;
  # the ${arr[@]+...} form is the portable guard.
  local cmd=(maestro ${DEVICE_ARGS[@]+"${DEVICE_ARGS[@]}"} test "$@" ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} --format junit --output "$out" --debug-output "$RUN_DIR/debug")
  if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" "${QA_REVIEW_SUITE_TIMEOUT:-3600}" "${cmd[@]}"; else "${cmd[@]}"; fi
}
# Portable per-flow timeout: macOS has no `timeout`; perl's alarm does the job.
with_timeout() { # secs, cmd...
  local secs="$1"; shift
  if [ -n "$TIMEOUT_BIN" ]; then "$TIMEOUT_BIN" "$secs" "$@"; else perl -e 'alarm shift; exec @ARGV' "$secs" "$@"; fi
}
run_flow() { # args: junit-out, flow
  local out="$1" flow="$2"
  with_timeout "${QA_REVIEW_FLOW_TIMEOUT:-900}" maestro ${DEVICE_ARGS[@]+"${DEVICE_ARGS[@]}"} test "$flow" ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} --format junit --output "$out" --debug-output "$RUN_DIR/debug"
}
# Per-flow mode: one maestro invocation per flow. Maestro validates the whole
# workspace before a multi-flow run and aborts everything on a single addMedia
# path it cannot resolve (0 flows executed); per-flow runs are immune and also
# isolate a wedged driver to one flow. Default on; QA_REVIEW_PER_FLOW=0 for the
# single-invocation mode.
PER_FLOW="${QA_REVIEW_PER_FLOW:-1}"
set +e
if [ "$PER_FLOW" = "1" ]; then
  SUITE_RC=0
  FAILED_LIST=""
  for f in "${SELECTED[@]}"; do
    name="$(basename "${f%.yaml}")"
    echo "qa-review: [$name] running"
    run_flow "$RUN_DIR/result-$name.xml" "$f"
    rc=$?
    if [ $rc -ne 0 ]; then SUITE_RC=1; FAILED_LIST="$FAILED_LIST $name"; echo "qa-review: [$name] FAILED (rc=$rc)"; else echo "qa-review: [$name] passed"; fi
  done
  if [ -n "$FAILED_LIST" ] && [ "${QA_REVIEW_NO_RETRY:-}" != "1" ]; then
    echo "qa-review: retrying failed flows once:$FAILED_LIST"
    for name in $FAILED_LIST; do
      run_flow "$RUN_DIR/result-retry-$name.xml" "flows/$name.yaml" && echo "qa-review: [$name] passed on retry" || echo "qa-review: [$name] failed again"
    done
  fi
else
  run_maestro "$RESULT" "${SELECTED[@]}"
  SUITE_RC=$?
fi
set -e

if [ "$PER_FLOW" != "1" ] && [ $SUITE_RC -ne 0 ] && [ "${QA_REVIEW_NO_RETRY:-}" != "1" ]; then
  echo "qa-review: suite had failures (rc=$SUITE_RC), retrying failed flows once"
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
  # The current run has no report.html yet, so the newest one on disk IS the
  # previous run. Taking line 2 reached back two runs, which pruning to 2 runs
  # usually deleted, so nothing was ever carried forward.
  PREV="$(ls -t "$HOME_DIR"/runs/*/report.html 2>/dev/null | sed -n 1p || true)"
  node "$SCRIPT_DIR/build-report.mjs" \
    --project "$PROJECT" \
    --manifest "$REPO/.maestro/journeys.manifest.json" \
    --config "$CONFIG" \
    --debug "$RUN_DIR/debug" \
    --junit "$JUNITS" \
    --out "$RUN_DIR/report.html" \
    --build "run $(date +%Y-%m-%d\ %H:%M)" \
    ${FINGERPRINT:+--buildinfo "$RUN_DIR/build.json"} \
    ${PREV:+--previous "$PREV"}
fi

node "$SCRIPT_DIR/prune-runs.mjs" --project "$PROJECT" --keep "${QA_REVIEW_KEEP_RUNS:-2}"

# The report is the deliverable, so the runner opens it instead of leaving that
# to whoever called the runner. QA_REVIEW_NO_OPEN=1 to keep it closed.
if [ "$BUILD_REPORT" = "1" ]; then
  "$SCRIPT_DIR/open-report.sh" "$RUN_DIR/report.html"
fi

echo "qa-review: done. Summary: $RUN_DIR/run-summary.json Report: $RUN_DIR/report.html"
