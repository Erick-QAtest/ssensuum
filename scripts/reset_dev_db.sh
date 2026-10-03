#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="$ROOT/api/ssensuum.db"

if [ -f "$DB" ]; then
  rm "$DB"
  echo "Removed $DB"
else
  echo "No local SQLite DB found."
fi

echo "Restart ./scripts/dev.sh to recreate and reseed the development database."
