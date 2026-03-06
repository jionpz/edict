#!/usr/bin/env python3
"""Check Done tasks have evidence, and write a report.

Outputs:
- data/evidence_report.json

This script does not mutate tasks_source.json; it only reports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TASKS_SOURCE = DATA_DIR / "tasks_source.json"
OUT_PATH = DATA_DIR / "evidence_report.json"


def _load_tasks() -> list[dict[str, Any]]:
    if not TASKS_SOURCE.exists():
        return []
    obj = json.loads(TASKS_SOURCE.read_text(encoding="utf-8"))
    if isinstance(obj, list):
        return [t for t in obj if isinstance(t, dict)]
    if isinstance(obj, dict) and isinstance(obj.get("tasks"), list):
        return [t for t in obj["tasks"] if isinstance(t, dict)]
    return []


def _evidence_fields(task: dict[str, Any]) -> dict[str, str]:
    found: dict[str, str] = {}
    for key in ("evidence", "evidencePath", "output", "outputPath"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            found[key] = value.strip()
    return found


def main() -> int:
    now = datetime.now(timezone.utc)
    tasks = _load_tasks()
    missing: list[dict[str, Any]] = []

    for task in tasks:
        if str(task.get("state", "")) != "Done":
            continue
        evidence = _evidence_fields(task)
        if evidence:
            continue
        missing.append(
            {
                "id": task.get("id"),
                "title": task.get("title"),
                "updatedAt": task.get("updatedAt"),
            }
        )

    report = {
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "doneCount": sum(1 for t in tasks if str(t.get("state", "")) == "Done"),
        "missingEvidenceCount": len(missing),
        "missing": missing,
    }

    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[evidence] wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
