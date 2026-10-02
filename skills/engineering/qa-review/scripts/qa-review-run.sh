#!/usr/bin/env bash
# qa-review suite runner. Runs Maestro flows for one project, on mobile (simulator)
# or web (Chrome), into a fresh run dir under ~/.qa-review/<project>/runs, then
# builds run-summary.json and report.html and prunes old runs.
# A config with "runner": "playwright" runs the repo's Playwright suite instead of
# Maestro and files its results the same way (references/playwright.md).
#
# Usage:
#   qa-review-run.sh --repo <path> [--tag smoke] [--flows "a.yaml b.yaml"] [--no-build] [--resume] [--scenarios-only]
#
# Reads .maestro/qa-review.config.json in the repo (or qa-review.config.json at
# the repo root when there is no .maestro folder):
#   project, platform (mobile|web), appId|url, buildCmd, installCmd, simulator
# Loads env from ~/.qa-review/<project>/.env (credentials, injected as maestro -e).
#
# Fail-loud rules: no step swallows its own error; anything bounded or skipped
# is echoed so "passed" never quietly means "did not run".
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- teardown: never leave maestro/JVM children or node orphans behind ---
# Runs on any exit (success, failure, Ctrl-C, timeout). Terminates this run's own
# child processes, then sweeps machine-wide node orphans (dead nx daemons, orphaned
# jest runs, dev servers with no listener) so a qa-review run can't grow the leak.
# The launchd guard (com.jarrhey.reap-node-leaks) is the backstop for a SIGKILLed session.
cleanup() {
  local ec=$?
  pkill -TERM -P $$ 2>/dev/null || true
  [ -x "$HOME/.claude/scripts/reap-node-leaks.sh" ] && bash "$HOME/.claude/scripts/reap-node-leaks.sh" >/dev/null 2>&1 || true
  return $ec
}
trap cleanup EXIT INT TERM

# The iOS simulator sometimes shuts down mid-suite (seen twice on Sep 27, cause
# unrecorded). Every later flow then failed as "device unreachable" in seconds,
# so one shutdown sank the whole run. Boot it back before each flow instead.
ensure_sim_booted() {
  [ "$PLATFORM" = "web" ] || [ "$PLATFORM" = "android" ] && return 0
  local udid="${QA_REVIEW_UDID:-}"
  [ -n "$udid" ] || udid="$(xcrun simctl list devices booted 2>/dev/null | grep -oE '[0-9A-F-]{36}' | head -1)"
  [ -n "$udid" ] || return 0
  if ! xcrun simctl list devices 2>/dev/null | grep -F "$udid" | grep -q "(Booted)"; then
    echo "qa-review: simulator $udid was not booted; booting it before the next flow"
    xcrun simctl boot "$udid" >/dev/null 2>&1 || true
    xcrun simctl bootstatus "$udid" -b >/dev/null 2>&1 || true
    sleep 5
  fi
}
REPO="" TAG="" FLOWS="" BUILD_REPORT=1
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2;;
    --tag) TAG="$2"; shift 2;;
    --flows) FLOWS="$2"; shift 2;;
    --no-build) BUILD_REPORT=0; shift;;
    --resume) RESUME=1; shift;;
    --scenarios-only) SCENARIOS_ONLY=1; shift;;
    *) echo "qa-review: unknown arg $1" >&2; exit 1;;
  esac
done
RESUME="${RESUME:-0}"
SCENARIOS_ONLY="${SCENARIOS_ONLY:-0}"
[ -n "$REPO" ] || { echo "qa-review: --repo <path> required" >&2; exit 1; }
# Absolute from here on: later steps cd elsewhere, and a relative --repo .
# then pointed the report at a manifest that is not there.
REPO="$(cd "$REPO" && pwd)"
# One run per machine at a time. Two runners share the device driver and each
# kills the other's session ("Device server died", every flow red in ~80ms),
# which is how a forgotten background run poisoned a whole Android pass.
OTHER_RUNS=""
for pid in $(pgrep -f 'qa-review-run.sh' || true); do
  # Skip this run, its parent, and its own subshells (same command line).
  [ "$pid" = "$$" ] || [ "$pid" = "$PPID" ] && continue
  [ "$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')" = "$$" ] && continue
  OTHER_RUNS="$OTHER_RUNS $pid"
done
if [ -n "$OTHER_RUNS" ] && [ "${QA_REVIEW_ALLOW_PARALLEL:-}" != "1" ]; then
  echo "qa-review: another qa-review run is active (pid $(echo $OTHER_RUNS | tr '\n' ' ')). Stop it first, or set QA_REVIEW_ALLOW_PARALLEL=1 for separate devices." >&2
  exit 1
fi
# QA_REVIEW_CONFIG picks another config in the same repo (e.g. an Android one
# beside the iOS default).
CONFIG="${QA_REVIEW_CONFIG:-$REPO/.maestro/qa-review.config.json}"
[ -n "${QA_REVIEW_CONFIG:-}" ] || [ -f "$CONFIG" ] || CONFIG="$REPO/qa-review.config.json"
case "$CONFIG" in /*) ;; *) CONFIG="$(cd "$REPO" && pwd)/$CONFIG";; esac
[ -f "$CONFIG" ] || { echo "qa-review: $CONFIG missing, run qa-review setup first" >&2; exit 1; }

jqget() { node -e "const c=require('$CONFIG');process.stdout.write(String(c['$1']??''))"; }
PROJECT="$(jqget project)"; PLATFORM="$(jqget platform)"
APP_ID="$(jqget appId)"; URL="$(jqget url)"
BUILD_CMD="$(jqget buildCmd)"; INSTALL_CMD="$(jqget installCmd)"
SIMULATOR="$(jqget simulator)"; SIMULATOR="${SIMULATOR:-iPhone 17}"
[ -n "$PROJECT" ] || { echo "qa-review: config has no project name" >&2; exit 1; }
RUNNER="$(jqget runner)"; RUNNER="${RUNNER:-maestro}"
# The manifest sits beside the config, wherever that is.
MANIFEST="$(dirname "$CONFIG")/journeys.manifest.json"

HOME_DIR="$HOME/.qa-review/$PROJECT"
# --resume reuses the newest run dir so a suite that died mid-way (a wedged driver,
# a crash) picks up where it stopped instead of restarting from zero. A flow with a
# passing result in that dir is skipped below. No prior dir => a fresh run.
if [ "$RESUME" = "1" ]; then
  RUN_DIR="$(ls -dt "$HOME_DIR"/runs/*/ 2>/dev/null | head -1)"; RUN_DIR="${RUN_DIR%/}"
  [ -n "$RUN_DIR" ] || RUN_DIR="$HOME_DIR/runs/$(date +%Y%m%d-%H%M%S)"
  echo "qa-review: resuming into $RUN_DIR"
else
  RUN_DIR="$HOME_DIR/runs/$(date +%Y%m%d-%H%M%S)"
fi
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

# Summary, report, prune, open: the same closing steps for every runner.
finish_run() {
  node "$SCRIPT_DIR/summarize-run.mjs" --run "$RUN_DIR"

  if [ "$BUILD_REPORT" = "1" ]; then
    GAPS=""; [ -f "$RUN_DIR/gaps.json" ] && GAPS="$RUN_DIR/gaps.json"
    JUNITS="$(ls "$RUN_DIR"/result*.xml 2>/dev/null | tr '\n' ',' | sed 's/,$//')"
    # The current run has no report.html yet, so the newest one on disk IS the
    # previous run. Taking line 2 reached back two runs, which pruning to 2 runs
    # usually deleted, so nothing was ever carried forward.
    PREV="$(ls -t "$HOME_DIR"/runs/*/report.html 2>/dev/null | sed -n 1p || true)"
    node "$SCRIPT_DIR/build-report.mjs" \
      --project "$PROJECT" \
      --manifest "$MANIFEST" \
      --config "$CONFIG" \
      --debug "$RUN_DIR/debug" \
      --junit "$JUNITS" \
      --out "$RUN_DIR/report.html" \
      --build "run $(date +%Y-%m-%d\ %H:%M)" \
      ${FINGERPRINT:+--buildinfo "$RUN_DIR/build.json"} \
      ${GAPS:+--gaps "$GAPS"} \
      ${PREV:+--previous "$PREV"}
  fi

  node "$SCRIPT_DIR/prune-runs.mjs" --project "$PROJECT" --keep "${QA_REVIEW_KEEP_RUNS:-2}"

  # The report is the deliverable, so the runner opens it instead of leaving that
  # to whoever called the runner. QA_REVIEW_NO_OPEN=1 to keep it closed.
  if [ "$BUILD_REPORT" = "1" ]; then
    "$SCRIPT_DIR/open-report.sh" "$RUN_DIR/report.html"
  fi

  echo "qa-review: done. Summary: $RUN_DIR/run-summary.json Report: $RUN_DIR/report.html"
}

write_fingerprint() { # arg: "<kind> <hash>", empty for none
  if [ -n "$1" ]; then
    node -e "
      const fs=require('fs');
      const [kind,...rest]=process.argv[1].split(' ');
      fs.writeFileSync('$RUN_DIR/build.json', JSON.stringify({kind,hash:rest.join(' '),at:new Date().toISOString()},null,2)+'\\n');
    " "$1"
    echo "qa-review: build fingerprint ${1%% *} ${1##* }"
  else
    echo "qa-review: NOTE no build fingerprint for platform $PLATFORM; carried evidence will expire instead of counting green"
  fi
}

# Playwright runner: the repo's own suite does the driving. Its config lists
# scripts/playwright-reporter.mjs, which files one result per spec plus the
# screenshots into this run dir. --tag becomes --grep @<tag>, --flows are spec
# paths. The test repo's commit says nothing about the deployed build under
# test, so the fingerprint comes from config "fingerprintCmd" (prints an id
# for the build it found) or is left out.
if [ "$RUNNER" = "playwright" ]; then
  FP_CMD="$(jqget fingerprintCmd)"
  FINGERPRINT=""
  if [ -n "$FP_CMD" ]; then
    FP="$(cd "$REPO" && eval "$FP_CMD" 2>/dev/null | tail -1 || true)"
    [ -n "$FP" ] && FINGERPRINT="commit $FP"
  fi
  write_fingerprint "$FINGERPRINT"
  PW_ARGS=()
  [ -n "$TAG" ] && PW_ARGS+=(--grep "@$TAG")
  [ "$RESUME" = "1" ] && PW_ARGS+=(--last-failed)
  for f in $FLOWS; do PW_ARGS+=("$f"); done
  echo "qa-review: playwright runner, npx playwright test ${PW_ARGS[*]:-}"
  set +e
  (cd "$REPO" && QA_REVIEW_RUN_DIR="$RUN_DIR" QA_REVIEW_PROJECT="$PROJECT" npx playwright test ${PW_ARGS[@]+"${PW_ARGS[@]}"})
  SUITE_RC=$?
  set -e
  [ $SUITE_RC -eq 0 ] && echo "qa-review: playwright suite passed" || echo "qa-review: playwright suite had failures (rc=$SUITE_RC)"
  ls "$RUN_DIR"/result*.xml >/dev/null 2>&1 || { echo "qa-review: no results in $RUN_DIR. Is scripts/playwright-reporter.mjs in the Playwright config's reporter list?" >&2; exit 1; }
  finish_run
  exit 0
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
  # Build/install/seed commands can target the exact simulator (several may be booted).
  export QA_REVIEW_UDID="$UDID"
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

# Seed: a project can reset its test data before every run (config "seedCmd").
# Its KEY=VALUE output lines (fresh fixture ids) are merged into the project .env
# and reloaded, so a deleted seed post never breaks the next run. A failed seed
# stops the run: flows over missing fixtures would fail for the wrong reason.
SEED_CMD="$(jqget seedCmd)"
if [ -n "$SEED_CMD" ] && [ "${QA_REVIEW_SKIP_SEED:-}" != "1" ] && [ "$RESUME" != "1" ]; then
  echo "qa-review: seeding test data (seedCmd). Set QA_REVIEW_SKIP_SEED=1 to skip."
  mkdir -p "$RUN_DIR"
  (cd "$REPO" && eval "$SEED_CMD") > "$RUN_DIR/seed.log" 2>&1 || { echo "qa-review: seed FAILED, see $RUN_DIR/seed.log" >&2; exit 1; }
  grep -E '^[A-Z][A-Z0-9_]*=' "$RUN_DIR/seed.log" | node "$SCRIPT_DIR/merge-env.mjs" "$HOME_DIR/.env"
  ENV_ARGS=(); ENV_COUNT=0
  while IFS='=' read -r k v; do
    [ -n "$k" ] && [[ "$k" != \#* ]] || continue
    v="${v%\"}"; v="${v#\"}"
    ENV_ARGS+=(-e "$k=$v"); ENV_COUNT=$((ENV_COUNT+1))
  done < "$HOME_DIR/.env"
  echo "qa-review: reloaded $ENV_COUNT env vars after seeding"
elif [ -n "$SEED_CMD" ]; then
  echo "qa-review: SKIPPED seed step (QA_REVIEW_SKIP_SEED=1 or --resume); using the fixtures already in .env"
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
      # The JS bundle ships beside the binary: a JS-only change leaves the
      # executable untouched, so hash both or a new build looks like the old one.
      local bundle=""
      [ -f "$container/main.jsbundle" ] && bundle="$container/main.jsbundle"
      printf 'binary %s' "$(cat "$container/$exe" ${bundle:+"$bundle"} | shasum -a 256 | awk '{print $1}')"
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
write_fingerprint "$FINGERPRINT"

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
    # Config "excludeFlows": globs for throwaway flows (screenshot scripts, one-off
    # checks) that are not part of the suite.
    node "$SCRIPT_DIR/config-glob.mjs" "$CONFIG" excluded "$base" && continue
    if [ -n "$TAG" ]; then
      grep -qE "^  - $TAG\$" "$f" || continue
    fi
    SELECTED+=("$f")
  done
fi
# Scenarios (config "scenarios"): flows a project runs through its own ordered
# script are left out of the one-by-one loop and run as a unit below. Full runs
# only; --flows or --tag runs the named flows directly.
RUN_SCENARIOS=0
if [ -z "$FLOWS" ] && [ -z "$TAG" ]; then
  SCEN_FLOWS="$(node "$SCRIPT_DIR/scenarios.mjs" "$CONFIG" flows)"
  if [ -n "$SCEN_FLOWS" ]; then
    RUN_SCENARIOS=1
    KEEP=()
    for f in ${SELECTED[@]+"${SELECTED[@]}"}; do
      n="$(basename "${f%.yaml}")"
      printf '%s\n' "$SCEN_FLOWS" | grep -qx "$n" || KEEP+=("$f")
    done
    SELECTED=(${KEEP[@]+"${KEEP[@]}"})
    # --scenarios-only: run just the scenario scripts (their flows) this time.
    [ "$SCENARIOS_ONLY" = "1" ] && SELECTED=()
    echo "qa-review: $(printf '%s\n' "$SCEN_FLOWS" | grep -c .) flow(s) run inside scenarios, not one by one"
  fi
fi
[ ${#SELECTED[@]} -gt 0 ] || [ "$RUN_SCENARIOS" = "1" ] || { echo "qa-review: no flows selected (tag=$TAG)" >&2; exit 1; }

# Web flows carry their own url: header, so guard every selected flow's target too,
# not only the config value.
for f in ${SELECTED[@]+"${SELECTED[@]}"}; do
  for u in $(grep -hoE '^\s*(url|-\s*openLink):\s*\S+' "$f" | awk '{print $NF}' | tr -d '"'"'"'"'); do
    "$SCRIPT_DIR/guard-env.sh" "$u" >/dev/null
  done
done
echo "qa-review: running ${#SELECTED[@]} flow(s): ${SELECTED[*]:-}"

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
# Per-flow setup: config "flowSetup" maps a flow-name glob to a command that
# prepares that flow's own fixtures (a harness script that creates a page, a
# circle history, a set of role accounts). Its KEY=VALUE output lines reach only
# that flow, as extra -e vars, and win over the project .env. A failed setup is
# recorded as the flow's failure with the setup log, so it never reads as a pass.
flow_setup_cmd() { node "$SCRIPT_DIR/config-glob.mjs" "$CONFIG" setup "$1"; }
run_flow() { # args: junit-out, flow
  local out="$1" flow="$2" name setup extra=()
  name="$(basename "$flow")"
  setup="$(flow_setup_cmd "$name")"
  if [ -n "$setup" ]; then
    local log="$RUN_DIR/setup-${name%.yaml}.log"
    echo "qa-review: [$name] setup: $setup"
    if ! (cd "$REPO" && eval "$setup") > "$log" 2>&1; then
      echo "qa-review: [$name] setup FAILED, see $log"
      printf '<?xml version="1.0"?><testsuites><testsuite name="setup" tests="1" failures="1"><testcase id="%s" name="%s"><failure>ENV: flow setup failed (%s), see %s</failure></testcase></testsuite></testsuites>' "${name%.yaml}" "${name%.yaml}" "$setup" "$log" > "$out"
      return 1
    fi
    while IFS='=' read -r k v; do extra+=(-e "$k=$v"); done < <(grep -E '^[A-Z][A-Z0-9_]*=' "$log")
  fi
  with_timeout "${QA_REVIEW_FLOW_TIMEOUT:-900}" maestro ${DEVICE_ARGS[@]+"${DEVICE_ARGS[@]}"} test "$flow" ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} ${extra[@]+"${extra[@]}"} --format junit --output "$out" --debug-output "$RUN_DIR/debug"
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
  for f in ${SELECTED[@]+"${SELECTED[@]}"}; do
    name="$(basename "${f%.yaml}")"
    # Resume: a flow that already has a passing result in this run dir is skipped,
    # so a re-invoke after a wedge only runs what is left.
    if [ "$RESUME" = "1" ] && [ -f "$RUN_DIR/result-$name.xml" ] && ! grep -q "<failure\|<error" "$RUN_DIR/result-$name.xml"; then
      echo "qa-review: [$name] already passed, skipping (resume)"
      continue
    fi
    # Driver-wedge recovery: the iOS XCUITest runner wedges ("device became
    # unreachable") and poisons the next flow. Kill any stale runner first so each
    # flow starts clean. No-op on platforms without it.
    # Android: a driver left from the previous flow can still hold the device
    # socket, so stop it and drop the port forwards. Do NOT uninstall it: a
    # reinstall per flow was too slow on an emulator and failed the connect
    # ("Device server died during 'deviceInfo'") on nearly every flow.
    if [ "$PLATFORM" = "android" ]; then
      adb -s "$SERIAL" shell am force-stop dev.mobile.maestro >/dev/null 2>&1 || true
      adb -s "$SERIAL" shell am force-stop dev.mobile.maestro.test >/dev/null 2>&1 || true
      adb -s "$SERIAL" forward --remove-all >/dev/null 2>&1 || true
      sleep 2
    fi
    if [ "$PLATFORM" != "web" ] && [ "$PLATFORM" != "android" ]; then
      pkill -9 -f UITests-Runner >/dev/null 2>&1 || true
      sleep 3
      ensure_sim_booted
    fi
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

# Scenarios: each project script runs as one unit against this simulator, with
# its per-flow results filed into this run dir. Config "scenarioEnv" is exported
# for them (target env, API base). Resume skips a scenario whose flows all passed.
if [ "$RUN_SCENARIOS" = "1" ]; then
  eval "$(node -e "const c=require('$CONFIG');for(const [k,v] of Object.entries(c.scenarioEnv||{}))console.log('export '+k+'='+JSON.stringify(String(v)))")"
  export E2E_IOS_UDID="${UDID:-}"
  while IFS=$'\t' read -r sname scmd; do
    [ -z "$sname" ] && continue
    owned="$(node "$SCRIPT_DIR/scenarios.mjs" "$CONFIG" owned "$sname")"
    if [ "$RESUME" = "1" ]; then
      allpass=1
      for fl in $owned; do
        [ -f "$RUN_DIR/result-$fl.xml" ] && ! grep -q "<failure\|<error" "$RUN_DIR/result-$fl.xml" || allpass=0
      done
      [ "$allpass" = "1" ] && { echo "qa-review: [scenario $sname] already passed, skipping (resume)"; continue; }
    fi
    art="$RUN_DIR/scenario-$sname"; rm -rf "$art"; mkdir -p "$art"
    [ "$PLATFORM" != "web" ] && [ "$PLATFORM" != "android" ] && { pkill -9 -f UITests-Runner >/dev/null 2>&1 || true; sleep 3; }
    ensure_sim_booted
    echo "qa-review: [scenario $sname] running"
    set +e
    (cd "$REPO" && E2E_ARTIFACT_DIR="$art" with_timeout "${QA_REVIEW_SCENARIO_TIMEOUT:-2700}" bash -c "$scmd") > "$RUN_DIR/scenario-$sname.log" 2>&1
    src=$?
    set -e
    node "$SCRIPT_DIR/scenarios.mjs" collect "$art" "$RUN_DIR" "$sname" "$src" $owned
    [ $src -eq 0 ] && echo "qa-review: [scenario $sname] passed" || { echo "qa-review: [scenario $sname] FAILED (rc=$src)"; SUITE_RC=1; }
  done < <(node "$SCRIPT_DIR/scenarios.mjs" "$CONFIG" list)
fi

finish_run
