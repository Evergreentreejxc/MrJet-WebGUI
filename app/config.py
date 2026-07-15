"""
Application configuration and constants.

All hardcoded values, paths, URLs, and status strings are centralized here.
"""

from typing import Final
import os

# ============================================================
# Paths
# ============================================================
DOWNLOAD_DIR: Final[str] = r"D:\IDM Download\Adult video"
PROJECT_ROOT: Final[str] = os.getcwd()
STATIC_DIR: Final[str] = os.path.join(PROJECT_ROOT, "static")
QUEUE_FILE: Final[str] = os.path.join(PROJECT_ROOT, "download_queue.json")

# ============================================================
# MissAV mirror domains (ordered by preference; tried in order)
# When one domain is blocked by Cloudflare, the next is used.
# ============================================================
MISSAV_MIRRORS: Final[list[str]] = [
    "https://missav.ai/",
    "https://missav.com/",
    "https://missav.ws/",
    "https://missav.cc/",
    "https://missav.net/",
]

# ============================================================
# Timing (seconds)
# ============================================================
STALL_TIMEOUT: Final[int] = 30         # how long without progress before considering stalled
CACHE_POLL_INTERVAL: Final[int] = 1    # seconds between cache-folder polls
CACHE_POLL_ATTEMPTS: Final[int] = 60   # max polls when starting a task manually
CACHE_POLL_ATTEMPTS_AUTO: Final[int] = 20  # max polls during auto-start
UI_REFRESH_DELAY: Final[int] = 5       # delay between UI refreshes while downloading
AUTO_START_NOTICE_DELAY: Final[int] = 2  # time to show notice before auto-start

# ============================================================
# Task status constants
# ============================================================
class Status:
    """Central source of truth for all task status markdown strings."""
    NOT_STARTED: str = ":gray-background[Not Started]"
    DOWNLOADING: str = ":orange-background[Downloading]"
    SUCCESS: str = ":green-background[Success]"
    FIXING: str = ":blue-background[Fixing]"
    COMPLETED: str = ":green-background[Completed]"
    FAILED: str = ":red-background[Failed]"
    FAILED_LOG_MISSING: str = ":red-background[Failed - Log Missing]"
    TAKEOVER_FAILED: str = ":red-background[Takeover Failed]"
    CACHE_INVALID: str = ":red-background[Cache Invalid]"
    FIX_FAILED: str = ":red-background[Fix Failed]"
    RETRYING: str = ":yellow-background[Retrying (mirror switch)]"

    # Set of statuses considered "finished" for cleanup
    FINISHED: frozenset = frozenset({
        COMPLETED, SUCCESS, FAILED, FAILED_LOG_MISSING,
        TAKEOVER_FAILED, CACHE_INVALID, FIX_FAILED,
    })

    # Set of statuses that are still active
    ACTIVE: frozenset = frozenset({DOWNLOADING, NOT_STARTED, RETRYING})

# ============================================================
# Download progress thresholds
# ============================================================
STALL_PROGRESS_THRESHOLD: Final[float] = 0.95  # progress >= 95% before triggering takeover