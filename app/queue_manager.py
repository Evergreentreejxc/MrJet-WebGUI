"""
Queue management – load / save / manipulate the persistent download queue.

The queue is a dict[str, TaskDict] persisted as JSON on disk.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from app.config import QUEUE_FILE, Status


# Typed dict alias for readability
TaskDict = Dict[str, Any]


def _default_task(display_name: str) -> TaskDict:
    """Return a new task entry with default values."""
    return {
        "DisplayName": display_name,
        "Created Date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Status": Status.NOT_STARTED,
        "Log": "",
        "Progress_Download": 0.0,
        "LastProgressValue": -1.0,
        "LastProgressTime": 0.0,
        "CacheFolder": None,
    }


def load_queue() -> Dict[str, TaskDict]:
    """Load the queue from disk; return empty dict on failure / missing."""
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_queue(queue: Dict[str, TaskDict]) -> None:
    """Persist the queue to disk."""
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=4, ensure_ascii=False)


def create_task(display_name: str, full_url: str) -> TaskDict:
    """Factory: create a new task dict."""
    return _default_task(display_name)


def update_task(queue: Dict[str, TaskDict], url: str, **updates) -> None:
    """Merge *updates* into the task entry at *url*."""
    if url in queue:
        queue[url].update(updates)


def is_any_downloading(queue: Dict[str, TaskDict]) -> bool:
    """Return True if at least one task has downloading status."""
    return any(t["Status"] == Status.DOWNLOADING for t in queue.values())


def find_next_not_started(queue: Dict[str, TaskDict]) -> str | None:
    """Return the URL of the first Not Started task, or None."""
    for url, task in queue.items():
        if task["Status"] == Status.NOT_STARTED:
            return url
    return None


def finished_task_urls(queue: Dict[str, TaskDict]) -> list[str]:
    """Return a list of URLs whose status is a finished state."""
    return [url for url, t in queue.items() if t["Status"] not in Status.ACTIVE]


def remove_tasks(queue: Dict[str, TaskDict], urls: list[str]) -> None:
    """Delete every URL in *urls* from the queue."""
    for url in urls:
        queue.pop(url, None)