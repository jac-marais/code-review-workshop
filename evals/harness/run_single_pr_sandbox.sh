#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: run_single_pr_sandbox.sh VALIDATION_COPY COMMAND [ARG ...]" >&2
  exit 2
fi

validation_copy=$(cd "$1" && pwd -P)
shift

if [[ ! -d "$validation_copy/.git" ]]; then
  echo "validation copy must contain its own .git directory" >&2
  exit 1
fi

exec docker run --rm \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 256 \
  --memory 2g \
  --cpus 2 \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  --tmpfs /dev/shm:rw,nosuid,nodev,size=512m \
  --volume "$validation_copy:/workspace:rw" \
  --env CI=1 \
  --env HOME=/tmp/home \
  --env PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
  code-review-single-pr-fixture:1 \
  "$@"
