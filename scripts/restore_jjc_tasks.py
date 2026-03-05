#!/usr/bin/env python3
"""Restore JJC-* tasks into data/tasks_source.json.

Why:
- JJC tasks are canonical "edicts" (旨意) and should remain visible.
- tasks_source.json can be accidentally overwritten by sync scripts.

This script scans data/tasks/JJC-* folders (and optional index files under data/)
then merges missing JJC tasks back into tasks_source.json.

It is safe to run repeatedly.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import re

from file_lock import atomic_json_read, atomic_json_write

BASE = pathlib.Path(__file__).resolve().parent.parent
DATA = BASE / "data"
TASKS_DIR = DATA / "tasks"
TASKS_FILE = DATA / "tasks_source.json"


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def load_tasks() -> list[dict]:
    return atomic_json_read(TASKS_FILE, [])


def save_tasks(tasks: list[dict]) -> None:
    atomic_json_write(TASKS_FILE, tasks)


def normalize_title(raw: str) -> str:
    t = (raw or "").strip().lstrip("#").strip()
    t = re.sub(r"^JJC-\d{8}-\d{3}[｜\|\-—:\s]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t or "未命名旨意"


def extract_title_from_md(md_path: pathlib.Path) -> str | None:
    try:
        for line in md_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("#"):
                return normalize_title(line)
            if line:
                break
    except Exception:
        return None
    return None


def best_effort_title(task_id: str) -> str:
    # 1) Prefer data/<id>-*.md index file
    for p in sorted(DATA.glob(f"{task_id}-*.md")):
        title = extract_title_from_md(p)
        if title:
            return title

    # 2) Then look inside task folder for any md heading
    folder = TASKS_DIR / task_id
    if folder.is_dir():
        for p in sorted(folder.glob("*.md")):
            title = extract_title_from_md(p)
            if title:
                return title

    return task_id


def main() -> None:
    tasks = load_tasks()
    by_id = {t.get("id"): t for t in tasks if isinstance(t, dict)}

    if not TASKS_DIR.is_dir():
        raise SystemExit(f"tasks dir not found: {TASKS_DIR}")

    jjc_ids = sorted(
        [p.name for p in TASKS_DIR.iterdir() if p.is_dir() and p.name.startswith("JJC-")]
    )

    restored = 0
    for task_id in jjc_ids:
        if task_id in by_id:
            continue

        title = best_effort_title(task_id)
        tasks.insert(
            0,
            {
                "id": task_id,
                "title": title,
                "official": "太子",
                "org": "太子",
                "state": "Taizi",
                "now": "已恢复显示：请更新最新进展/状态",
                "eta": "-",
                "block": "无",
                "output": "",
                "ac": "",
                "flow_log": [
                    {
                        "at": now_iso(),
                        "from": "系统",
                        "to": "太子",
                        "remark": "🔁 重启后恢复显示：从 data/tasks 目录补回旨意卡片",
                    }
                ],
                "updatedAt": now_iso(),
            },
        )
        restored += 1

    # Keep stable order: JJC first, then others; within JJC sort by id desc
    jjc = [t for t in tasks if str(t.get("id", "")).startswith("JJC-")]
    other = [t for t in tasks if not str(t.get("id", "")).startswith("JJC-")]
    jjc.sort(key=lambda x: str(x.get("id", "")), reverse=True)

    save_tasks(jjc + other)
    print(json.dumps({"ok": True, "restored": restored, "jjcCount": len(jjc)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
