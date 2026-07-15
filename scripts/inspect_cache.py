"""Deep inspection of all cache folder contents."""
import os
import tempfile
import glob

base = tempfile.gettempdir()
folders = glob.glob(os.path.join(base, "??????????"))
for f in sorted(folders):
    if not os.path.isdir(f):
        continue
    name = os.path.basename(f)
    if not (name.isalnum() and len(name) == 10):
        continue
    print(f"\n=== {name} ===")
    for root, dirs, files in os.walk(f):
        rel = os.path.relpath(root, f)
        if files:
            print(f"  {rel}/: {len(files)} files")
            for fn in files[:10]:
                fp = os.path.join(root, fn)
                size = os.path.getsize(fp)
                print(f"    {fn} ({size} bytes)")
            if len(files) > 10:
                print(f"    ... and {len(files)-10} more")