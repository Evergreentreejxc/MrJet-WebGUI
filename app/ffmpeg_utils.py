"""
FFmpeg utilities – video repair (faststart) and takeover (concat segments).

All functions operate on file paths and return success / failure indicators.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import Optional


# ---------------------------------------------------------------------------
# Video repair (faststart remux)
# ---------------------------------------------------------------------------

def fix_video_and_overwrite(input_file: str) -> bool:
    """
    Losslessly remux *input_file* with ``-movflags faststart`` so the video
    is seekable.  The original file is overwritten.
    """
    dir_name = os.path.dirname(input_file)
    fd, temp_name = tempfile.mkstemp(suffix=".mp4", dir=dir_name)
    os.close(fd)

    cmd = ["ffmpeg", "-y", "-i", input_file, "-c", "copy", "-movflags", "faststart", temp_name]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        shutil.move(temp_name, input_file)
        return True
    except subprocess.CalledProcessError as e:
        print(f"!! Fix failed: {input_file}\n{e.stderr.decode(errors='replace')}")
        if os.path.exists(temp_name):
            os.remove(temp_name)
        return False


def find_and_fix_video(display_name: str, download_dir: str) -> bool:
    """
    Find a file inside *download_dir* whose name (case-insensitive, hyphens
    stripped) contains *display_name*, then run *fix_video_and_overwrite* on it.
    Returns True on success.
    """
    def normalize_id(text: str) -> str:
        return text.lower().replace("-", "")

    normalized_name = normalize_id(display_name)
    for filename in os.listdir(download_dir):
        full = os.path.join(download_dir, filename)
        if not os.path.isfile(full):
            continue
        file_base, _ = os.path.splitext(filename)
        if normalized_name in normalize_id(file_base):
            return fix_video_and_overwrite(full)
    return False


# ---------------------------------------------------------------------------
# Takeover – merge cached ts/mp4 segments into a single .mp4 via ffmpeg concat
# ---------------------------------------------------------------------------

def takeover_with_ffmpeg(cache_folder: str, output_path: str) -> bool | str:
    """
    Attempt to take over a partial download by merging all .mp4 segments
    inside *cache_folder* into *output_path*.

    Returns
    -------
    True        – merge succeeded
    False       – merge failed or no segments
    "keep_going"– segments are still being written, caller should retry later
    """
    try:
        print(f"FFmpeg takeover started: {cache_folder}")

        # Initial segment list
        initial_files = [f for f in os.listdir(cache_folder) if f.endswith(".mp4")]
        time.sleep(10)  # give writer a moment to stabilise
        final_files = [f for f in os.listdir(cache_folder) if f.endswith(".mp4")]

        print(f"Initial: {len(initial_files)} segments, 10s later: {len(final_files)} segments.")

        if len(initial_files) != len(final_files):
            print("!! Segments still growing – mrjet may still be running. Deferring takeover.")
            return "keep_going"

        if not final_files:
            return False

        # Sort segments by embedded numeric index
        def extract_number(name: str) -> int:
            m = re.search(r"\d+", name)
            return int(m.group()) if m else 0

        sorted_files = sorted(final_files, key=extract_number)

        # Build concat playlist
        playlist = os.path.join(cache_folder, "ffmpeg_playlist.txt")
        with open(playlist, "w", encoding="utf-8") as f:
            for name in sorted_files:
                f.write(f"file '{os.path.join(cache_folder, name)}'\n")

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", playlist, "-c", "copy", output_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        print(f"FFmpeg merge successful: {output_path}")
        shutil.rmtree(cache_folder, ignore_errors=True)
        return True

    except subprocess.CalledProcessError as e:
        print(f"!! FFmpeg concat failed: {e.stderr.decode(errors='replace')}")
        # Don't remove cache folder on failure
        return False
    except Exception as e:
        print(f"!! Unexpected error during takeover: {e}")
        if os.path.exists(cache_folder):
            shutil.rmtree(cache_folder, ignore_errors=True)
        return False