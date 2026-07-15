"""
Manual FFmpeg takeover — merge cached mrjet segments into a complete MP4.

Usage:
    python scripts/manual_takeover.py <cache_folder_path> [output_name]

If output_name is omitted, uses "manual_takeover_output.mp4".
"""

import os
import re
import shutil
import subprocess
import sys

from app.config import DOWNLOAD_DIR


def takeover(cache_folder: str, output_path: str) -> bool:
    """Merge all .mp4 segments in cache_folder into output_path."""
    playlist_files = os.path.join(cache_folder, "playlist_files")
    if os.path.isdir(playlist_files):
        target_dir = playlist_files
    else:
        target_dir = cache_folder

    mp4_files = sorted(
        [f for f in os.listdir(target_dir) if f.endswith(".mp4")],
        key=lambda x: int(re.search(r"\d+", x).group() or 0) if re.search(r"\d+", x) else 0,
    )

    if not mp4_files:
        print("No .mp4 segments found!")
        return False

    print(f"Found {len(mp4_files)} segments in {target_dir}:")
    for f in mp4_files:
        print(f"  - {f}")

    playlist = os.path.join(target_dir, "ffmpeg_playlist.txt")
    with open(playlist, "w", encoding="utf-8") as pf:
        for name in mp4_files:
            pf.write(f"file '{os.path.join(target_dir, name)}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", playlist, "-c", "copy", output_path]
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print(f"\n✅ Success! Output: {output_path}")
        return True
    else:
        print(f"\n❌ FFmpeg failed:\n{result.stderr.decode(errors='replace')}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cache = sys.argv[1]
    if not os.path.isdir(cache):
        print(f"Error: {cache} is not a valid directory")
        sys.exit(1)

    output_name = sys.argv[2] if len(sys.argv) > 2 else "manual_takeover_output.mp4"
    output_path = os.path.join(DOWNLOAD_DIR, output_name)

    takeover(cache, output_path)