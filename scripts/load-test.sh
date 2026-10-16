#!/usr/bin/env bash
# Usage: scripts/load-test.sh <base-url> [seconds]   e.g. scripts/load-test.sh http://localhost:8080 60
# Only asks for bugs that exist, so the error panel in Grafana stays at zero.
base="${1:?base url}"; end=$((SECONDS + ${2:-60}))
host="Host: ${HOST_HEADER:-bugtrack.local}"
get() { curl -s -o /dev/null -H "$host" "$base$1"; }

# real bug ids from the list endpoint
read -r -a ids < <(curl -s -H "$host" "$base/api/bugs" | grep -o '"id":[0-9]*' | cut -d: -f2 | tr '\n' ' ')
[ ${#ids[@]} -gt 0 ] || { echo "no bugs found, add a few in the app first"; exit 1; }
echo "found ${#ids[@]} bugs, sending requests for ${2:-60}s"

while [ $SECONDS -lt $end ]; do
  get /api/bugs &
  get /api/bugs/stats &
  for _ in 1 2 3; do
    id=${ids[RANDOM % ${#ids[@]}]}
    get "/api/bugs/$id" &
  done
  wait; sleep 0.1
done
