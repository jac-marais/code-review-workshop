#!/usr/bin/env bash
set -euo pipefail

mkdir -p /tmp/home /tmp/npm-cache /tmp/npm-logs
cp -a /opt/npm-cache/. /tmp/npm-cache/
export HOME=/tmp/home
export npm_config_cache=/tmp/npm-cache
export npm_config_logs_dir=/tmp/npm-logs
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

if [[ ! -d /workspace/.git ]]; then
  echo "validation copy needs separate Git administration" >&2
  exit 1
fi

npm ci --offline --ignore-scripts
exec "$@"
