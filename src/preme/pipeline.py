#!/usr/bin/env python3
"""
Preme Clipping End-to-End Pipeline
1. Scrapes high-hook clips
2. Generates click-worthy hook headline & caption
3. Renders 1080x1920 Reel with blurred background, hook, and official overlay (max 15.0s)
4. Uploads to Google Drive queue folder (1NuU7Jc3zLVnd08UZh6U-2QrlWxOmEWXr)
   (Supports both Google Service Account API in Cloud and gdrive CLI on Local)
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fetch_clips import fetch_top_twitch_clips, download_clip, save_processed_clip, load_processed_ids
from hook_engine import generate_hook_and_caption
from render_engine import render_preme_reel

# Google Drive Queue Folder ID (Preme Clipping Reels)
GDRIVE_QUEUE_FOLDER_ID = (os.getenv("PREME_GDRIVE_FOLDER_ID") or "1NuU7Jc3zLVnd08UZh6U-2QrlWxOmEWXr").strip()
GDRIVE_SA_KEY = os.getenv("GDRIVE_SA_KEY", "")

MANIFEST_LOG = BASE_DIR / "preme_queue_manifest.json"
TMP_OUT_DIR = Path("/tmp/preme_rendered_reels")

def upload_via_service_account(file_path: str, parent_folder_id: str) -> str:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    try:
        sa_info = json.loads(GDRIVE_SA_KEY)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build("drive", "v3", credentials=creds)
        file_metadata = {
            "name": os.path.basename(file_path),
            "parents": [parent_folder_id]
        }
        media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True)
        file_obj = service.files().create(body=file_metadata, media_body=media, fields="id, name").execute()
        drive_id = file_obj.get("id", "")
        print(f"  ☁️ [Drive API] Uploaded {os.path.basename(file_path)} (ID: {drive_id})")
        return drive_id
    except Exception as e:
        print(f"  ❌ Drive API upload failed: {e}")
        return ""

def upload_via_gdrive_cli(file_path: str, parent_folder_id: str) -> str:
    cmd = ["gdrive", "mutate", "upload", file_path, "--parent", parent_folder_id, "--json"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        out = res.stdout.strip()
        print(f"  ☁️ [gdrive CLI] {out}")
        if "ID: " in out:
            return out.split("ID: ")[-1].replace(")", "").strip()
    else:
        print(f"  ❌ gdrive CLI error: {res.stderr}")
    return ""

def upload_to_drive(file_path: str, parent_folder_id: str) -> str:
    if GDRIVE_SA_KEY:
        return upload_via_service_account(file_path, parent_folder_id)
    if shutil.which("gdrive"):
        return upload_via_gdrive_cli(file_path, parent_folder_id)
    print("  ⚠️ No Google Drive upload method available.")
    return ""

def run_pipeline(batch_size: int = 3, time_range: str = "all"):
    print("=" * 60)
    print(f"🚀 STARTING PREME CLIPPING AUTOMATION BATCH (Target: {batch_size} reels)")
    print("=" * 60)

    TMP_OUT_DIR.mkdir(parents=True, exist_ok=True)

    clips = fetch_top_twitch_clips(limit=batch_size, time_range=time_range)
    if not clips:
        print("ℹ️ No new clips to process at this time.")
        return

    manifest = []
    if MANIFEST_LOG.exists():
        try:
            with open(MANIFEST_LOG, "r") as f:
                manifest = json.load(f)
        except Exception:
            manifest = []

    success_count = 0
    for i, clip in enumerate(clips):
        clip_id = clip["id"]
        title = clip["title"]
        print(f"\n[{i+1}/{len(clips)}] Processing Clip #{clip_id}: '{title}' ({clip['views']} views, {clip['duration']}s)...")

        # 1. Download raw clip
        raw_video = download_clip(clip, output_dir=Path("/tmp/preme_raw_clips"))
        if not raw_video or not os.path.exists(raw_video):
            print(f"  ⚠️ Skipping clip #{clip_id} due to download error.")
            continue

        # 2. Generate Hook & Caption
        hook_data = generate_hook_and_caption(title)
        h1 = hook_data["hook_line1"]
        h2 = hook_data["hook_line2"]
        caption = hook_data["caption"]
        print(f"  🎯 Hook L1: {h1}")
        print(f"  🎯 Hook L2: {h2}")

        # 3. Render 1080x1920 Reel (15s max)
        out_reel_path = str(TMP_OUT_DIR / f"preme_reel_{clip_id}.mp4")
        ok = render_preme_reel(
            input_video=raw_video,
            output_mp4=out_reel_path,
            hook_line1=h1,
            hook_line2=h2,
            duration=clip["duration"],
            max_duration=15.0
        )
        if not ok:
            print(f"  ⚠️ Skipping clip #{clip_id} due to render error.")
            continue

        # 4. Upload to Google Drive Queue
        drive_id = upload_to_drive(out_reel_path, GDRIVE_QUEUE_FOLDER_ID)

        # 5. Record metadata
        entry = {
            "clip_id": clip_id,
            "title": title,
            "original_url": clip["url"],
            "views": clip["views"],
            "duration": clip["duration"],
            "hook_line1": h1,
            "hook_line2": h2,
            "caption": caption,
            "drive_id": drive_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "queued_in_drive"
        }
        save_processed_clip(clip_id, entry)
        manifest.append(entry)
        with open(MANIFEST_LOG, "w") as f:
            json.dump(manifest, f, indent=2)

        success_count += 1
        print(f"  🎉 Clip #{clip_id} processed, rendered & queued successfully!")

    print("\n" + "=" * 60)
    print(f"🏁 BATCH COMPLETE: {success_count}/{len(clips)} reels processed and queued in Drive!")
    print("=" * 60)

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run_pipeline(batch_size=count)
