#!/usr/bin/env python3
"""Generate Edict "health report" from tasks_source.json.

Outputs:
- data/health_report.json

This script is intentionally dependency-free.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TASKS_SOURCE = DATA_DIR / "tasks_source.json"
OUT_PATH = DATA_DIR / "health_report.json"


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        # Accept both Z and offset forms.
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return None


@dataclass(frozen=True)
class HealthCounts:
    total: int
    not_done: int
    stalled_6h: int
    stalled_24h: int
    done_missing_evidence: int


def _load_tasks() -> list[dict[str, Any]]:
    if not TASKS_SOURCE.exists():
        return []
    try:
        obj = json.loads(TASKS_SOURCE.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(obj, list):
        return [t for t in obj if isinstance(t, dict)]
    if isinstance(obj, dict) and isinstance(obj.get("tasks"), list):
        return [t for t in obj["tasks"] if isinstance(t, dict)]
    return []


def _has_evidence(task: dict[str, Any]) -> bool:
    """Heuristic: a Done task should reference an evidence/output path."""
    for key in ("evidence", "evidencePath", "output", "outputPath"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return True
    return False


def _is_blocked(task: dict[str, Any]) -> bool:
    """Treat tasks with explicit block reason as 'blocked' (exclude from stall alerts)."""
    block = task.get("block")
    if not isinstance(block, str):
        return False
    block = block.strip()
    return bool(block) and block not in ("无", "-", "none", "None")


def _hours_since_updated(task: dict[str, Any], now: datetime) -> float | None:
    dt = _parse_iso(str(task.get("updatedAt")) if task.get("updatedAt") else None)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() / 3600


def compute_counts(tasks: list[dict[str, Any]], now: datetime) -> HealthCounts:
    not_done_tasks = [t for t in tasks if str(t.get("state", "")) != "Done"]

    stalled_6h = 0
    stalled_24h = 0
    for t in not_done_tasks:
        if _is_blocked(t):
            continue
        h = _hours_since_updated(t, now)
        if h is None:
            continue
        if h >= 6:
            stalled_6h += 1
        if h >= 24:
            stalled_24h += 1

    done_missing_evidence = 0
    for t in tasks:
        if str(t.get("state", "")) == "Done" and not _has_evidence(t):
            done_missing_evidence += 1

    return HealthCounts(
        total=len(tasks),
        not_done=len(not_done_tasks),
        stalled_6h=stalled_6h,
        stalled_24h=stalled_24h,
        done_missing_evidence=done_missing_evidence,
    )


def main() -> int:
    now = datetime.now(timezone.utc)
    tasks = _load_tasks()
    counts = compute_counts(tasks, now)

    # Extra signals for "self-evolution": dispatch failures and blocked backlog.
    blocked = []
    dispatch_errors = []
    for t in tasks:
        if _is_blocked(t) and str(t.get("state", "")) != "Done":
            blocked.append({"id": t.get("id"), "title": t.get("title"), "block": t.get("block"), "state": t.get("state")})
        sched = t.get("_scheduler") if isinstance(t.get("_scheduler"), dict) else {}
        if sched.get("lastDispatchStatus") == "error" or sched.get("lastDispatchError"):
            dispatch_errors.append({
                "id": t.get("id"),
                "title": t.get("title"),
                "state": t.get("state"),
                "error": sched.get("lastDispatchError"),
                "trigger": sched.get("lastDispatchTrigger"),
            })

    report = {
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "counts": {
            "total": counts.total,
            "notDone": counts.not_done,
            "stalled6h": counts.stalled_6h,
            "stalled24h": counts.stalled_24h,
            "doneMissingEvidence": counts.done_missing_evidence,
            "blockedNotDone": len(blocked),
            "dispatchErrors": len(dispatch_errors),
        },
        "top": {
            "blocked": blocked[:10],
            "dispatchErrors": dispatch_errors[:10],
        },
        "notes": {
            "stallRule": "Only count as stalled if state!=Done AND not blocked AND updatedAt older than threshold",
            "blockedRule": "block field non-empty and not in {无,-,none}",
            "evidenceRule": "Done tasks should include evidence/output path",
        },
    }

    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[health] wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
