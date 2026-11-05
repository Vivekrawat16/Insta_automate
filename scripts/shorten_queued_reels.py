#!/usr/bin/env python3
"""
Re-renders pending Preme reels into punchy 12-14 second short reels,
and updates them in-place in Google Drive.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

BASE_DIR = Path("/home/vivek/preme_clipping")
sys.path.insert(0, str(BASE_DIR))

from render_engine import render_preme_reel

MANIFEST_FILE = BASE_DIR / "preme_queue_manifest.json"

def main():
    if not os.path.exists(MANIFEST_FILE):
        print("Manifest not found")
        return

    with open(MANIFEST_FILE, "r") as f:
        manifest = json.load(f)

    pending = [item for item in manifest if item.get("status") == "queued_in_drive"]
    print(f"🎬 Found {len(pending)} pending reels to shorten to ~13-14 seconds...")

    TARGET_DURATION = 14.0

    for i, item in enumerate(pending):
        clip_id = item["clip_id"]
        raw_clip = str(BASE_DIR / "raw_clips" / f"clip_{clip_id}.mp4")
        out_reel = item["local_file"]
        drive_id = item.get("drive_id")
        h1 = item.get("hook_line1", "")
        h2 = item.get("hook_line2", "")

        print(f"\n[{i+1}/{len(pending)}] Shortening clip #{clip_id} to {TARGET_DURATION}s...")
        if not os.path.exists(raw_clip):
            print(f"  ❌ Raw clip not found: {raw_clip}")
            continue

        # Re-render to exact TARGET_DURATION
        ok = render_preme_reel(
            input_video=raw_clip,
            output_mp4=out_reel,
            hook_line1=h1,
            hook_line2=h2,
            duration=TARGET_DURATION,
            max_duration=TARGET_DURATION
        )

        if ok and drive_id:
            print(f"  ☁️ Updating Drive file in-place (ID: {drive_id})...")
            cmd = ["gdrive", "mutate", "update", drive_id, out_reel]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                print(f"  ✅ Drive file updated in-place!")
            else:
                print(f"  ⚠️ Drive update warning: {res.stderr}")

            item["duration"] = TARGET_DURATION

    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 60)
    print(f"🎉 SUCCESS: All {len(pending)} pending reels shortened to 14s and updated in Drive!")
    print("=" * 60)

if __name__ == "__main__":
    main()
