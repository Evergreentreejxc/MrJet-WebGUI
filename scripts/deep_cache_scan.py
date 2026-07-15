"""
Scan ALL mrjet cache folders in temp directory.
Read playlist_files JSON to find video segments and their actual paths.
Print complete details to help decide which cache can be merged.

Usage: python scripts/deep_cache_scan.py
"""
import json
import os
import tempfile
import glob

base = tempfile.gettempdir()
pattern = os.path.join(base, "??????????")
folders = glob.glob(pattern)

print("=== Scanning mrjet cache folders ===\n")

for f in sorted(folders):
    if not os.path.isdir(f):
        continue
    name = os.path.basename(f)
    if not (name.isalnum() and len(name) == 10):
        continue

    print(f"\n{'='*60}")
    print(f"Folder: {f}")
    print(f"Name: {name}")

    # List everything inside
    items = os.listdir(f)
    print(f"Contents: {items}")

    # Check playlist_files
    pl_path = os.path.join(f, "playlist_files")
    if os.path.exists(pl_path):
        size = os.path.getsize(pl_path)
        print(f"playlist_files size: {size} bytes")

        # Try reading as JSON
        try:
            with open(pl_path, "r", encoding="utf-8") as pf:
                data = json.load(pf)
            if isinstance(data, list):
                print(f"  Playlist entries: {len(data)}")
                for i, entry in enumerate(data[:3]):
                    filepath = entry.get("file", entry) if isinstance(entry, dict) else entry
                    if isinstance(filepath, str):
                        exists = os.path.exists(filepath) if not filepath.startswith(".") else "rel"
                        size_f = os.path.getsize(filepath) if exists is True else 0
                        print(f"    [{i}] {filepath} ({size_f} bytes, exists={exists})")
                if len(data) > 3:
                    print(f"    ... and {len(data)-3} more")
            elif isinstance(data, dict):
                print(f"  Playlist keys: {list(data.keys())[:5]}")
                # Try common keys
                for key in ["files", "segments", "items", "entries"]:
                    if key in data:
                        print(f"  {key}: {len(data[key])} items")
                        for item in data[key][:2]:
                            print(f"    {item}")
        except (json.JSONDecodeError, Exception) as e:
            # Read as plain text
            with open(pl_path, "r", encoding="utf-8", errors="ignore") as pf:
                text = pf.read(500)
            print(f"  Not valid JSON, raw content: {text}...")

    # Check for any .mp4 files recursively
    mp4_files = []
    for root, dirs, files in os.walk(f):
        for fn in files:
            if fn.endswith(".mp4") or fn.endswith(".ts") or fn.endswith(".m3u8"):
                fp = os.path.join(root, fn)
                mp4_files.append((fp, os.path.getsize(fp)))

    if mp4_files:
        print(f"\n  Video segments found: {len(mp4_files)}")
        for fp, sz in mp4_files[:5]:
            print(f"    {os.path.basename(fp)} ({sz/1024/1024:.1f} MB)")
        if len(mp4_files) > 5:
            print(f"    ... and {len(mp4_files)-5} more")
    else:
        print(f"\n  No video segments (.mp4/.ts/.m3u8) found")

    # Check parent subdirs
    subdirs = [d for d in os.listdir(f) if os.path.isdir(os.path.join(f, d))]
    if subdirs:
        print(f"  Subdirectories: {subdirs}")
        for sd in subdirs:
            sd_path = os.path.join(f, sd)
            sd_files = os.listdir(sd_path)
            print(f"    {sd}/: {len(sd_files)} items {sd_files[:10]}")

    print()