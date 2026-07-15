"""Scan all mrjet cache folders and print details about each one."""
import os
import glob
import tempfile

base = tempfile.gettempdir()
folders = glob.glob(os.path.join(base, "??????????"))
for f in sorted(folders):
    if not os.path.isdir(f):
        continue
    name = os.path.basename(f)
    if not (name.isalnum() and len(name) == 10):
        continue
    contents = os.listdir(f)
    mp4_count = 0
    for item in contents:
        item_path = os.path.join(f, item)
        if os.path.isdir(item_path):
            sub_files = os.listdir(item_path)
            mp4_sub = [x for x in sub_files if x.endswith('.mp4')]
            if mp4_sub:
                mp4_count += len(mp4_sub)
                print(f"  {name}/{item}/: {len(mp4_sub)} mp4 segments (e.g. {mp4_sub[0]})")
        elif item.endswith('.mp4'):
            mp4_count += 1
    print(f"  {name}: total {mp4_count} mp4 segments, items: {contents[:5]}...")