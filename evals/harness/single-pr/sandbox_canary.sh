#!/usr/bin/env bash
set -euo pipefail

test -z "${HOST_REVIEW_SECRET:-}"
test ! -e /run/host-services
test ! -S /var/run/docker.sock
test ! -S "${SSH_AUTH_SOCK:-/missing-agent-socket}"

if touch /sandbox-root-write-canary 2>/dev/null; then
  echo "container root filesystem is writable" >&2
  exit 1
fi

if curl --connect-timeout 1 --silent http://169.254.169.254/latest/meta-data/ >/dev/null 2>&1; then
  echo "cloud metadata is reachable" >&2
  exit 1
fi

if curl --connect-timeout 1 --silent http://host.docker.internal:43123/ >/dev/null 2>&1; then
  echo "host service is reachable" >&2
  exit 1
fi

echo "sandbox canaries denied host capabilities"
