"""
Download orchestration — wraps Mr. Banana engine (Jable) and legacy mrjet CLI (MissAV).

The primary engine is now Mr. Banana's ``MovieDownloader`` for jable.tv.
MissAV remains supported via the legacy ``mrjet`` subprocess path.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import tempfile
import threading
import time
import uuid
from typing import Optional

from app.config import DOWNLOAD_DIR, STATIC_DIR, MISSAV_MIRRORS, JABLE_BASE_URL
from app.config import STALL_TIMEOUT, STALL_PROGRESS_THRESHOLD, Platform
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
    """Extract just the video ID from any input form."""
    if user_input.startswith("http"):
        cleaned = user_input.split("#")[0].strip("/")
        return cleaned.split("/")[-1] or user_input
    return user_input.strip()


def detect_platform(user_input: str) -> str:
    """Guess the platform from user input. Returns Platform.JABLE or Platform.MISSAV.

    - Full jable.tv URL → Jable
    - Full missav.* URL → MissAV
    - Bare code (e.g. 'SSIS-001') → default to MissAV (backward compatible)
    """
    lowered = user_input.lower()
    if "jable.tv" in lowered:
        return Platform.JABLE
    if "missav" in lowered:
        return Platform.MISSAV
    # Bare code → MissAV (original behavior)
    return Platform.MISSAV


def build_video_url(video_id: str, platform: str = Platform.MISSAV, mirror_index: int = 0) -> str:
    """Build a full URL from *video_id*."""
    if platform == Platform.JABLE:
        return f"{JABLE_BASE_URL}{video_id}/"
    else:
        return f"{MISSAV_MIRRORS[mirror_index]}{video_id}"


def parse_display_name(user_input: str) -> tuple[str, str, str]:
    """
    Return ``(full_url, display_name, platform)``.
    """
    if user_input.startswith("http"):
        cleaned = user_input.split("#")[0].strip("/")
        display = cleaned.split("/")[-1] or user_input
        platform = Platform.JABLE if "jable" in user_input.lower() else Platform.MISSAV
        return user_input, display, platform
    else:
        platform = detect_platform(user_input)
        return build_video_url(user_input, platform), user_input, platform


# ---------------------------------------------------------------------------
# Cache folder detection (legacy — only needed for mrjet / MissAV)
# ---------------------------------------------------------------------------

def find_mrjet_cache_folders() -> list[str]:
    temp_dir = tempfile.gettempdir()
    pattern = os.path.join(temp_dir, "??????????")
    all_folders = glob.glob(pattern)
    return [f for f in all_folders if os.path.isdir(f) and os.path.basename(f).isalnum() and len(os.path.basename(f)) == 10]


def poll_for_cache_folder(before: set[str], max_attempts: int, interval: int = 1) -> Optional[str]:
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
# Launch engine (Mr. Banana for Jable, mrjet CLI for MissAV)
# ---------------------------------------------------------------------------

def launch_mrjet(video_url: str) -> tuple[Optional[str], Optional[str]]:
    """Legacy: start mrjet CLI for MissAV. Returns (status_md, log_link_md)."""
    log_id = uuid.uuid4()
    log_file_path = os.path.join(STATIC_DIR, f"{log_id}.log")

    command = f'mrjet --url "{video_url}" --output_dir "{DOWNLOAD_DIR}"'
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                env=env,
            )
        log_link = f"[logfile](./static/{log_id}.log)"
        return Status.DOWNLOADING, log_link
    except Exception as e:
        print(f"!! Failed to launch mrjet: {e}")
        return Status.FAILED, None


def launch_jable_download(video_url: str, task: TaskDict, queue: dict, url: str) -> None:
    """
    Start a Jable download via Mr. Banana engine in a background thread.
    Progress is recorded directly into the task dict.
    """
    from mr_banana.downloader import MovieDownloader

    try:
        downloader = MovieDownloader()

        # Progress callback that updates the task in-place
        def progress_cb(current: int, total: int, speed: str, total_bytes: int):
            if total > 0:
                progress = min(current / total, 1.0)
                update_task(queue, url, Progress_Download=progress)
                update_task(queue, url, LastProgressValue=progress,
                            LastProgressTime=time.time())

        # Run download in a daemon thread so Streamlit can keep polling
        def _download_thread():
            try:
                output_path = downloader.download(
                    url=video_url,
                    output_dir=DOWNLOAD_DIR,
                    progress_callback=progress_cb,
                    filename_format="{id}",
                )
                if output_path and os.path.exists(output_path):
                    update_task(queue, url, Status=Status.SUCCESS,
                                Progress_Download=1.0)
                    print(f"Jable download complete: {output_path}")
                else:
                    update_task(queue, url, Status=Status.FAILED)
            except Exception as e:
                print(f"!! Jable download failed: {e}")
                update_task(queue, url, Status=Status.FAILED)

        t = threading.Thread(target=_download_thread, daemon=True)
        t.start()
    except Exception as e:
        print(f"!! Failed to initialize Mr. Banana downloader: {e}")
        update_task(queue, url, Status=Status.FAILED)


# ---------------------------------------------------------------------------
# Log-parsing state reader (for legacy mrjet / MissAV only)
# ---------------------------------------------------------------------------

def read_log_state(log_link: str) -> tuple[str, float]:
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
    download_matches = re.findall(r"Download\s*:\s*\[[^\]]*\]\s*([0-9.]+)%", content)
    if download_matches:
        progress = float(download_matches[-1]) / 100.0
    build_matches = re.findall(r"Build\s*:\s*\[[^\]]*\]\s*([0-9.]+)%", content)
    if build_matches and float(build_matches[-1]) >= 100.0:
        return Status.SUCCESS, 1.0
    if ("Error" in content or "ERROR:" in content) and "Logging error" not in content:
        return Status.FAILED, progress
    return Status.DOWNLOADING, progress


def _parse_log_filename(log_link: str) -> Optional[str]:
    try:
        return log_link.split("/static/")[1].split(")")[0]
    except (IndexError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Cloudflare / domain-block detection
# ---------------------------------------------------------------------------

def _check_cf_blocked(log_link: str) -> bool:
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
    indicators = ["cloudflare", "403", "just a moment", "max retries reached",
                  "failed to fetch data", "http status: 403"]
    return any(indicator in content for indicator in indicators)


def _patch_queue_url(queue: dict, old_url: str, new_url: str) -> None:
    if old_url in queue and old_url != new_url:
        queue[new_url] = queue.pop(old_url)


# ---------------------------------------------------------------------------
# Stall detection
# ---------------------------------------------------------------------------

def _try_bind_cache(queue: dict, url: str, task: TaskDict) -> None:
    now = time.time()
    last_check = task.get("_cache_check_time", 0)
    if last_check == 0:
        update_task(queue, url, _cache_check_time=now,
                    _cache_baseline=list(find_mrjet_cache_folders()))
        return
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
        task.pop("_cache_check_time", None)
        task.pop("_cache_baseline", None)


def check_stall(task: TaskDict, current_progress: float) -> bool:
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
    current_status = task["Status"]

    # ------ DOWNLOADING -> check progress / stall / finish ------
    if current_status == Status.DOWNLOADING:
        platform = task.get("Platform", Platform.MISSAV)

        if platform == Platform.JABLE:
            # Mr. Banana already updates progress via callback — just check final state
            progress = task.get("Progress_Download", 0.0)
            if task.get("Progress_Download", 0.0) >= 1.0:
                return  # still DOWNLOADING, progress already 1.0 = working
            # No log parsing needed — Mr. Banana manages its own lifecycle
            if progress != task.get("LastProgressValue", -1.0):
                update_task(queue, url, LastProgressValue=progress, LastProgressTime=time.time())
            # Stall check for Jable
            if check_stall(task, progress):
                print(f"Stall detected for Jable task {task['DisplayName']}")
                update_task(queue, url, Status=Status.FAILED)
            return

        # MissAV (legacy mrjet) path
        status, progress = read_log_state(task.get("Log", ""))
        update_task(queue, url, Progress_Download=progress)

        if task.get("CacheFolder") is None:
            _try_bind_cache(queue, url, task)

        if progress != task.get("LastProgressValue", -1.0):
            update_task(queue, url, LastProgressValue=progress, LastProgressTime=time.time())

        # CF retry
        if status == Status.FAILED and _check_cf_blocked(task.get("Log", "")):
            mirror_idx = task.get("MirrorIndex", 0)
            if mirror_idx + 1 < len(MISSAV_MIRRORS):
                video_id = task.get("VideoID") or extract_video_id(url)
                new_url = build_video_url(video_id, Platform.MISSAV, mirror_idx + 1)
                print(f"CF blocked on mirror {mirror_idx}, retrying with mirror {mirror_idx + 1}")
                update_task(queue, url, Status=Status.RETRYING, MirrorIndex=mirror_idx + 1)
                return
            else:
                print(f"All mirrors exhausted for {task['DisplayName']}.")

        # Stall / takeover
        if check_stall(task, progress):
            print(f"Stall detected for {task['DisplayName']} – attempting takeover.")
            cache_folder = task.get("CacheFolder")
            if cache_folder and os.path.isdir(cache_folder):
                output = os.path.join(DOWNLOAD_DIR, f"{task['DisplayName']}.mp4")
                result = takeover_with_ffmpeg(cache_folder, output)
                if result is True:
                    update_task(queue, url, Status=Status.COMPLETED,
                                Log=task.get("Log", "") + " (Takeover)")
                    return
                elif result == "keep_going":
                    update_task(queue, url, LastProgressTime=time.time())
                    return
                else:
                    update_task(queue, url, Status=Status.TAKEOVER_FAILED)
                    return
            else:
                update_task(queue, url, Status=Status.CACHE_INVALID)
                return

        if status != Status.DOWNLOADING:
            update_task(queue, url, Status=status)
            return

    # ------ RETRYING -> restart with new mirror (MissAV only) ------
    if current_status == Status.RETRYING:
        mirror_idx = task.get("MirrorIndex", 1)
        video_id = task.get("VideoID") or extract_video_id(url)
        new_url = build_video_url(video_id, Platform.MISSAV, mirror_idx)
        _patch_queue_url(queue, url, new_url)
        status_md, log_link = launch_mrjet(new_url)
        update_task(queue, new_url, Status=status_md, Log=log_link,
                    LastProgressTime=time.time(), LastProgressValue=0.0)
        print(f"Restarted {task['DisplayName']} on mirror {mirror_idx}")
        return

    # ------ SUCCESS -> FIXING ------
    if current_status == Status.SUCCESS:
        update_task(queue, url, Status=Status.FIXING)

    # ------ FIXING -> run ffmpeg fix ------
    if current_status == Status.FIXING:
        ok = find_and_fix_video(task["DisplayName"], DOWNLOAD_DIR)
        update_task(queue, url, Status=Status.COMPLETED if ok else Status.FIX_FAILED)