#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Mexico_City")

if len(sys.argv) != 2:
    print("Usage: python3 scripts/configure_qa.py /path/to/ssensuum-qa-framework/.env")
    raise SystemExit(2)

path = Path(sys.argv[1]).expanduser().resolve()
if not path.exists():
    print(f"File not found: {path}")
    raise SystemExit(1)

now = datetime.now(TZ)
tomorrow = (now + timedelta(days=1)).date().isoformat()
free_start = f"{tomorrow}T13:00:00-06:00"

updates = {
    "SSENSUUM_WEB_BASE_URL": "http://localhost:3000",
    "SSENSUUM_API_BASE_URL": "http://localhost:8000",
    "QA_SERVICE_ID": "massage-special",
    "QA_SERVICE_NAME": "Masaje especial",
    "QA_THERAPIST_ID": "alex",
    "QA_THERAPIST_NAME": "Alex",
    "QA_AVAILABLE_DATE": tomorrow,
    "QA_AVAILABLE_TIME": "12:00",
    "QA_FREE_STARTS_AT": free_start,
    "QA_AGENDA_DATE": tomorrow,
}

lines = path.read_text(encoding="utf-8").splitlines()
seen: set[str] = set()
out: list[str] = []
for line in lines:
    if "=" in line and not line.lstrip().startswith("#"):
        key = line.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
            continue
    out.append(line)

if out and out[-1] != "":
    out.append("")
out.append("# Local SSENSUUM Sprint 1 seed")
for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}")

path.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Updated: {path}")
for key, value in updates.items():
    print(f"{key}={value}")
