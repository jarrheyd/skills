#!/usr/bin/env bash
# Refuses to run a scout suite against anything that looks like production.
# A target passes when it carries a non-production marker (dev, staging, test,
# qa, sandbox, uat, localhost, 127.0.0.1, *.local, a .dev bundle suffix).
# Override only by the USER exporting SCOUT_ALLOW_PROD=1 in their own shell.
#
#   guard-env.sh <target>     target = URL (web) or appId (mobile)
set -euo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  echo "guard-env: no target given (URL or appId)" >&2
  exit 1
fi

if [ "${SCOUT_ALLOW_PROD:-}" = "1" ]; then
  echo "guard-env: SCOUT_ALLOW_PROD=1 set by user, skipping the check for: $TARGET"
  exit 0
fi

lower="$(printf '%s' "$TARGET" | tr '[:upper:]' '[:lower:]')"
case "$lower" in
  *localhost*|*127.0.0.1*|*0.0.0.0*|*.local|*.local/*|*dev*|*staging*|*stage*|*test*|*qa*|*sandbox*|*uat*|*preview*)
    echo "guard-env: target looks non-production, proceeding: $TARGET"
    exit 0
    ;;
esac

cat >&2 <<EOF
guard-env: REFUSING to run against "$TARGET".
It carries no dev/staging/test marker, so it may be production. Scout only runs
against test or staging environments with test accounts. If this target really
is safe, the user (not the agent) can export SCOUT_ALLOW_PROD=1 and rerun.
EOF
exit 2
