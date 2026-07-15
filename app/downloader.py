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

from app.config import DOWNLOAD_DIR, STATIC_DIR, MISSAV_MIRRORS
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


def extract_video_id(user_input: str) -> str:
    """
    Extract just the video ID from any input form (URL or raw ID).

    Examples:
        'https://missav.ws/SSIS-001' -> 'SSIS-001'
        'SSIS-001'                   -> 'SSIS-001'
        'https://missav.ai/ssis-001' -> 'ssis-001'
    """
    if user_input.startswith("http"):
        cleaned = user_input.split("#")[0].strip("/")
        return cleaned.split("/")[-1] or user_input
    return user_input.strip()


def build_video_url(video_id: str, mirror_index: int = 0) -> str:
    """
    Build a full URL from *video_id* using the mirror at *mirror_index*.

    Raises IndexError if *mirror_index* is out of range.
    """
    return f"{MISSAV_MIRRORS[mirror_index]}{video_id}"


def parse_display_name(user_input: str) -> tuple[str, str]:
    """
    Given raw user input, return ``(full_url, display_name)``.

    If the input is not a full URL, it is prefixed with the **first** mirror
    (missav.ai) and the display name is the raw input.  Otherwise the last
    path segment is used.
    """
    if user_input.startswith("http"):
        cleaned = user_input.split("#")[0].strip("/")
        display = cleaned.split("/")[-1] or user_input
        return user_input, display
    else:
        return build_video_url(user_input), user_input


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
# Cloudflare / domain-block detection
# ---------------------------------------------------------------------------

def _check_cf_blocked(log_link: str) -> bool:
    """
    Read the mrjet log and return True if it looks like Cloudflare or a domain
    block was the cause of failure (so we can auto-retry on a different mirror).
    """
    if not log_link:
        return False
    log_file = _parse_log_filename(log_link)
    if log_file is None:
        return False
    log_path = os.path.join(STATIC_DIR, log_file)
    if not os.path.exists(log_path):
        return False
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
    except OSError:
        return False

    # Heuristics for Cloudflare / access-denied failures
    indicators = [
        "cloudflare",
        "403",               # HTTP 403 Forbidden
        "just a moment",     # Cloudflare challenge page title
        "max retries reached",
        "failed to fetch data",
        "http status: 403",
    ]
    return any(indicator in content for indicator in indicators)


def _patch_queue_url(queue: dict, old_url: str, new_url: str) -> None:
    """
    Replace a queue key *old_url* with *new_url*, preserving all task data.

    This is necessary when we retry with a different mirror domain because the
    URL itself is the dictionary key.
    """
    if old_url in queue and old_url != new_url:
        queue[new_url] = queue.pop(old_url)


# ---------------------------------------------------------------------------
# Stall detection
# ---------------------------------------------------------------------------

def _try_bind_cache(queue: dict, url: str, task: TaskDict) -> None:
    """
    Attempt to discover and bind the mrjet cache folder for the current task.

    Called once per UI cycle while status is DOWNLOADING and CacheFolder is None.
    The first call records the baseline snapshot; subsequent calls check for
    a single new 10-char folder.
    """
    now = time.time()
    last_check = task.get("_cache_check_time", 0)

    if last_check == 0:
        # First attempt — record baseline
        update_task(queue, url, _cache_check_time=now,
                    _cache_baseline=list(find_mrjet_cache_folders()))
        return

    # Wait at least 2 seconds between checks
    if now - last_check < 2:
        return

    update_task(queue, url, _cache_check_time=now)
    baseline = set(task.get("_cache_baseline", []))
    current = set(find_mrjet_cache_folders())
    new = current - baseline

    if len(new) == 1:
        folder = new.pop()
        update_task(queue, url, CacheFolder=folder)
        print(f"Async cache binding: {task['DisplayName']} -> {folder}")
        # Clean up tracking keys
        task.pop("_cache_check_time", None)
        task.pop("_cache_baseline", None)


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

        # ---- Async cache folder binding (non-blocking, retried each cycle) ----
        if task.get("CacheFolder") is None:
            _try_bind_cache(queue, url, task)

        # Track progress movement for stall detection
        if progress != task.get("LastProgressValue", -1.0):
            update_task(queue, url,
                        LastProgressValue=progress,
                        LastProgressTime=time.time())

        # ---- Cloudflare / domain-block detection & mirror retry ----
        if status == Status.FAILED and _check_cf_blocked(task.get("Log", "")):
            mirror_idx = task.get("MirrorIndex", 0)
            if mirror_idx + 1 < len(MISSAV_MIRRORS):
                video_id = task.get("VideoID") or extract_video_id(url)
                new_url = build_video_url(video_id, mirror_idx + 1)
                print(f"CF blocked on mirror {mirror_idx} ({MISSAV_MIRRORS[mirror_idx]}), "
                      f"retrying with mirror {mirror_idx + 1} ({MISSAV_MIRRORS[mirror_idx + 1]})")
                update_task(queue, url,
                            Status=Status.RETRYING,
                            MirrorIndex=mirror_idx + 1)
                return
            else:
                print(f"All {len(MISSAV_MIRRORS)} mirrors exhausted for {task['DisplayName']}.")

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

    # ------ RETRYING -> restart with new mirror URL ------
    if current_status == Status.RETRYING:
        mirror_idx = task.get("MirrorIndex", 1)
        video_id = task.get("VideoID") or extract_video_id(url)
        new_url = build_video_url(video_id, mirror_idx)

        _patch_queue_url(queue, url, new_url)

        status_md, log_link = launch_mrjet(new_url)
        update_task(queue, new_url,
                    Status=status_md,
                    Log=log_link,
                    LastProgressTime=time.time(),
                    LastProgressValue=0.0)
        print(f"Restarted {task['DisplayName']} on {MISSAV_MIRRORS[mirror_idx]}")
        return

    # ------ SUCCESS -> FIXING ------
    if current_status == Status.SUCCESS:
        update_task(queue, url, Status=Status.FIXING)

    # ------ FIXING -> run ffmpeg fix ------
    if current_status == Status.FIXING:
        ok = find_and_fix_video(task["DisplayName"], DOWNLOAD_DIR)
        update_task(queue, url,
                    Status=Status.COMPLETED if ok else Status.FIX_FAILED)