#!/usr/bin/env bash
# Run Caddy (public $PORT) and the Reflex backend (localhost only) together.
# If either exits, stop the other and exit so Railway restarts the container.
set -u

caddy run --config Caddyfile --adapter caddyfile &
reflex run --env prod --backend-only &

stopping=0
trap 'stopping=1; kill -TERM $(jobs -p) 2>/dev/null' TERM INT
wait -n
status=$?
kill -TERM $(jobs -p) 2>/dev/null
wait
# A requested stop is a clean exit; anything else reports the failure.
if [ "$stopping" = 1 ]; then exit 0; fi
exit "$status"
