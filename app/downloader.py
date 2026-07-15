"""
Download orchestration – launch mrjet, monitor logs, detect stalls, bind cache folders.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import tempfile
import time
import uuid
from typing import Optional

from app.config import DOWNLOAD_DIR, STATIC_DIR, BASE_URL
from app.config import STALL_TIMEOUT, STALL_PROGRESS_THRESHOLD
from app.config import Status
from app.queue_manager import TaskDict, update_task
from app.ffmpeg_utils import takeover_with_ffmpeg, find_and_fix_video


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------

def normalize_id(text: str) -> str:
    """Lower-case, no hyphens."""
    return text.lower().replace("-", "")


def parse_display_name(user_input: str) -> tuple[str, str]:
    """
    Given raw user input, return ``(full_url, display_name)``.

    If the input is not a full URL, it is prefixed with *BASE_URL* and the
    display name is the raw input.  Otherwise the last path segment is used.
    """
    if user_input.startswith("http"):
        cleaned = user_input.split("#")[0].strip("/")
        display = cleaned.split("/")[-1] or user_input
        return user_input, display
    else:
        return f"{BASE_URL}{user_input}", user_input


# ---------------------------------------------------------------------------
# Cache folder detection
# ---------------------------------------------------------------------------

def find_mrjet_cache_folders() -> list[str]:
    """
    Return all subdirectories inside the temp folder whose names are exactly
    10 alphanumeric characters (the typical mrjet cache pattern).
    """
    temp_dir = tempfile.gettempdir()
    pattern = os.path.join(temp_dir, "??????????")
    all_folders = glob.glob(pattern)
    return [f for f in all_folders if os.path.isdir(f) and os.path.basename(f).isalnum() and len(os.path.basename(f)) == 10]


def poll_for_cache_folder(before: set[str], max_attempts: int, interval: int = 1) -> Optional[str]:
    """
    Poll the temp directory up to *max_attempts* times for new mrjet cache
    folders that were not present in the *before* set.

    Returns the first new folder path, or None on timeout.
    """
    for i in range(max_attempts):
        time.sleep(interval)
        after = set(find_mrjet_cache_folders())
        new_folders = after - before
        if len(new_folders) == 1:
            path = new_folders.pop()
            print(f"Cache folder detected after {i + 1} seconds: {path}")
            return path
    return None


# ---------------------------------------------------------------------------
# Launch mrjet
# ---------------------------------------------------------------------------

def launch_mrjet(video_url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Start ``mrjet`` as a subprocess for *video_url*.

    Returns ``(status_markdown, log_link_markdown)``.
    On launch failure, *status* is ``Status.FAILED`` and *log_link* is ``None``.
    """
    log_id = uuid.uuid4()
    log_file_path = os.path.join(STATIC_DIR, f"{log_id}.log")

    command = f'mrjet --url "{video_url}" --output_dir "{DOWNLOAD_DIR}"'
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            proc = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                env=env,
            )
        # Quick check – if the process exits immediately with a non-zero code
        # the log will likely contain an error message.
        log_link = f"[logfile](./static/{log_id}.log)"
        return Status.DOWNLOADING, log_link
    except Exception as e:
        print(f"!! Failed to launch mrjet: {e}")
        return Status.FAILED, None


# ---------------------------------------------------------------------------
# Progress / status reading from log file
# ---------------------------------------------------------------------------

def read_log_state(log_link: str) -> tuple[str, float]:
    """
    Parse the mrjet log file referenced by *log_link* and return
    ``(status_markdown, progress_float_0_1)``.
    """
    if not log_link:
        return Status.NOT_STARTED, 0.0

    log_file = _parse_log_filename(log_link)
    if log_file is None:
        return Status.FAILED_LOG_MISSING, 0.0

    log_path = os.path.join(STATIC_DIR, log_file)
    if not os.path.exists(log_path):
        return Status.FAILED_LOG_MISSING, 0.0

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return Status.FAILED_LOG_MISSING, 0.0

    progress = 0.0
    # Download progress
    download_matches = re.findall(r"Download\s*:\s*\[[^\]]*\]\s*([0-9.]+)%", content)
    if download_matches:
        progress = float(download_matches[-1]) / 100.0

    # Build progress (100% = success)
    build_matches = re.findall(r"Build\s*:\s*\[[^\]]*\]\s*([0-9.]+)%", content)
    if build_matches and float(build_matches[-1]) >= 100.0:
        return Status.SUCCESS, 1.0

    # Error detection
    if "Error" in content or "ERROR:" in content:
        if "Logging error" not in content:
            return Status.FAILED, progress

    return Status.DOWNLOADING, progress


def _parse_log_filename(log_link: str) -> Optional[str]:
    """
    Extract the UUID log filename from a markdown log link like
    ``[logfile](./app/static/uuid.log)``.
    """
    try:
        # Format: [logfile](./app/static/<uuid>.log)
        return log_link.split("/static/")[1].split(")")[0]
    except (IndexError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Stall detection
# ---------------------------------------------------------------------------

def check_stall(task: TaskDict, current_progress: float) -> bool:
    """
    Return True when progress has not changed for more than *STALL_TIMEOUT*
    seconds *and* progress is >= *STALL_PROGRESS_THRESHOLD*.
    """
    last_val = task.get("LastProgressValue", -1.0)
    last_time = task.get("LastProgressTime", 0.0)

    if current_progress == last_val:
        if last_time and (time.time() - last_time > STALL_TIMEOUT):
            return current_progress >= STALL_PROGRESS_THRESHOLD
    return False


# ---------------------------------------------------------------------------
# High-level task state machine step
# ---------------------------------------------------------------------------

def step_task(url: str, task: TaskDict, queue: dict) -> None:
    """
    Advance one state-transition step for the given task.

    Called each UI loop so that state transitions happen without blocking.
    """
    current_status = task["Status"]

    # ------ DOWNLOADING -> check progress / stall / finish ------
    if current_status == Status.DOWNLOADING:
        status, progress = read_log_state(task.get("Log", ""))

        # Always update progress
        update_task(queue, url, Progress_Download=progress)

        # Track progress movement for stall detection
        if progress != task.get("LastProgressValue", -1.0):
            update_task(queue, url,
                        LastProgressValue=progress,
                        LastProgressTime=time.time())

        # Stall check
        if check_stall(task, progress):
            print(f"Stall detected for {task['DisplayName']} – attempting takeover.")
            cache_folder = task.get("CacheFolder")
            if cache_folder and os.path.isdir(cache_folder):
                output = os.path.join(DOWNLOAD_DIR, f"{task['DisplayName']}.mp4")
                result = takeover_with_ffmpeg(cache_folder, output)
                if result is True:
                    update_task(queue, url,
                                Status=Status.COMPLETED,
                                Log=task.get("Log", "") + " (Takeover)")
                    print(f"Takeover succeeded for {task['DisplayName']}.")
                    return
                elif result == "keep_going":
                    update_task(queue, url, LastProgressTime=time.time())
                    print("Takeover deferred – segments still growing.")
                    return
                else:
                    update_task(queue, url, Status=Status.TAKEOVER_FAILED)
                    return
            else:
                print(f"!! No valid cache folder for {task['DisplayName']}.")
                update_task(queue, url, Status=Status.CACHE_INVALID)
                return

        # Status change from the log (success / failed)
        if status != Status.DOWNLOADING:
            update_task(queue, url, Status=status)
            return

    # ------ SUCCESS -> FIXING ------
    if current_status == Status.SUCCESS:
        update_task(queue, url, Status=Status.FIXING)

    # ------ FIXING -> run ffmpeg fix ------
    if current_status == Status.FIXING:
        ok = find_and_fix_video(task["DisplayName"], DOWNLOAD_DIR)
        update_task(queue, url,
                    Status=Status.COMPLETED if ok else Status.FIX_FAILED)