#!/usr/bin/env bash
# Refuses to run a scout suite against anything that looks like production.
# A target passes when one of its hostname labels or bundle-id segments IS a
# non-production marker (dev, staging, stage, test, qa, sandbox, uat, preview,
# local, localhost, 127.0.0.1, 0.0.0.0) or starts with one followed by a digit
# or a hyphen (dev2, staging-eu, qa-1). Substrings inside ordinary words do not
# count: app.devhub.com, latest.acme.com and backstage.io are refused.
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
# Host part of a URL, or the whole thing for a bundle id.
host="$lower"
case "$host" in
  *://*) host="${host#*://}";;
esac
host="${host%%/*}"; host="${host%%\?*}"; host="${host#*@}"; host="${host%%:*}"

ok=0
case "$host" in
  localhost|127.0.0.1|0.0.0.0|*.local) ok=1;;
esac
if [ $ok -eq 0 ]; then
  IFS='.-' read -ra LABELS <<< "$host"
  for label in "${LABELS[@]}"; do
    case "$label" in
      dev|develop|development|staging|stage|stg|test|testing|qa|sandbox|uat|preview|local|localhost) ok=1; break;;
      dev[0-9]*|staging[0-9]*|stage[0-9]*|test[0-9]*|qa[0-9]*|uat[0-9]*|preview[0-9]*) ok=1; break;;
    esac
  done
fi

if [ $ok -eq 1 ]; then
  echo "guard-env: target looks non-production, proceeding: $TARGET"
  exit 0
fi

cat >&2 <<MSG
guard-env: REFUSING to run against "$TARGET".
No hostname label or bundle-id segment is a dev/staging/test marker, so it may be
production. Scout only runs against test or staging environments with test accounts.
If this target really is safe, the user (not the agent) can export SCOUT_ALLOW_PROD=1 and rerun.
MSG
exit 2
