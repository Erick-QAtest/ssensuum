#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> SSENSUUM bootstrap"

if [ ! -f "$ROOT/api/.env" ]; then
  cp "$ROOT/api/.env.example" "$ROOT/api/.env"
  echo "Created api/.env"
fi

if [ ! -f "$ROOT/web/.env.local" ]; then
  cp "$ROOT/web/.env.local.example" "$ROOT/web/.env.local"
  echo "Created web/.env.local"
fi

if [ ! -d "$ROOT/api/.venv" ]; then
  python3 -m venv "$ROOT/api/.venv"
fi

"$ROOT/api/.venv/bin/pip" install -r "$ROOT/api/requirements.txt"

(cd "$ROOT/web" && npm install)

echo
printf '%s\n' "Bootstrap complete." "Run: ./scripts/dev.sh"
