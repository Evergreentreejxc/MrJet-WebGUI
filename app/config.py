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
# Supported platforms
# ============================================================
class Platform:
    JABLE: str = "jable"       # jable.tv (Mr. Banana engine)
    MISSAV: str = "missav"     # MissAV (legacy mrjet CLI)
    ALL: list[str] = ["jable", "missav"]

# ============================================================
# MissAV mirror domains (ordered by preference)
# ============================================================
MISSAV_MIRRORS: Final[list[str]] = [
    "https://missav.ai/",
    "https://missav.com/",
    "https://missav.ws/",
    "https://missav.cc/",
    "https://missav.net/",
]

# ============================================================
# Jable.tv settings
# ============================================================
JABLE_BASE_URL: Final[str] = "https://jable.tv/videos/"

# ============================================================
# Timing (seconds)
# ============================================================
STALL_TIMEOUT: Final[int] = 30
CACHE_POLL_INTERVAL: Final[int] = 1
CACHE_POLL_ATTEMPTS: Final[int] = 60
CACHE_POLL_ATTEMPTS_AUTO: Final[int] = 20
UI_REFRESH_DELAY: Final[int] = 5
AUTO_START_NOTICE_DELAY: Final[int] = 2

# ============================================================
# Task status constants
# ============================================================
class Status:
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

    FINISHED: frozenset = frozenset({
        COMPLETED, SUCCESS, FAILED, FAILED_LOG_MISSING,
        TAKEOVER_FAILED, CACHE_INVALID, FIX_FAILED,
    })

    ACTIVE: frozenset = frozenset({DOWNLOADING, NOT_STARTED, RETRYING})

# ============================================================
# Download progress thresholds
# ============================================================
STALL_PROGRESS_THRESHOLD: Final[float] = 0.95