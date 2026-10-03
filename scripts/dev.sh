#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -x "$ROOT/api/.venv/bin/uvicorn" ]; then
  echo "Run ./scripts/bootstrap.sh first."
  exit 1
fi

cleanup() {
  echo
  echo "Stopping SSENSUUM..."
  kill "${API_PID:-0}" "${WEB_PID:-0}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd "$ROOT/api"
  "$ROOT/api/.venv/bin/uvicorn" app.main:app --reload --host 127.0.0.1 --port 8000
) &
API_PID=$!

(
  cd "$ROOT/web"
  npm run dev
) &
WEB_PID=$!

echo "SSENSUUM starting..."
echo "Web: http://localhost:3000"
echo "API: http://localhost:8000/docs"

wait
