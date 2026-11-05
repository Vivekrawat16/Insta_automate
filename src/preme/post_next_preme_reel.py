#!/usr/bin/env python3
"""
Preme Reel Poster for @coool_verse_
Uploads the next pending Preme reel to Instagram and records the post URL for clipping.net tracking.
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from instagrapi import Client

BASE_DIR = Path(__file__).resolve().parent
SESSION_FILE = os.getenv("INSTA_SESSION_FILE") or str(BASE_DIR / "insta_session_coool_verse.json")
MANIFEST_FILE = BASE_DIR / "preme_queue_manifest.json"
DRIVE_ARCHIVE_ID = (os.getenv("PREME_GDRIVE_ARCHIVE_ID") or "1E3xbmMxuMykWskFagbQ155mn5Dq1QWfG").strip()

def get_client() -> Client:
    cl = Client()
    session_json = os.getenv("INSTA_SESSION_JSON")
    if session_json:
        try:
            cl.set_settings(json.loads(session_json))
            return cl
        except Exception as e:
            print(f"Warning: Failed to load INSTA_SESSION_JSON ({e})")

    if os.path.exists(SESSION_FILE):
        cl.load_settings(SESSION_FILE)
        if hasattr(cl, "sessionid") and cl.sessionid:
            cl.login_by_sessionid(cl.sessionid)
            return cl

    raise FileNotFoundError(f"No valid session found (checked INSTA_SESSION_JSON env and {SESSION_FILE})")

def move_in_drive(file_id: str, new_parent_id: str):
    """Moves a file in Google Drive to the archive folder."""
    if shutil.which("gdrive"):
        cmd = ["gdrive", "mutate", "mv", file_id, new_parent_id]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print(f"  ☁️ Moved reel in Google Drive to Archive folder!")
            return
        else:
            print(f"  ⚠️ Warning: Could not move file in Drive: {res.stderr}")

def post_next_reel():
    if not os.path.exists(MANIFEST_FILE):
        print("❌ No manifest file found.")
        return

    with open(MANIFEST_FILE, "r") as f:
        manifest = json.load(f)

    pending = [item for item in manifest if item.get("status") == "queued_in_drive"]
    if not pending:
        print("ℹ️ No pending reels in queue! Run pipeline.py to generate more reels.")
        return

    target = pending[0]
    reel_path = target.get("local_file", "")
    caption = target["caption"]
    drive_id = target.get("drive_id", "")

    if not os.path.exists(reel_path):
        print(f"❌ Local video file missing: {reel_path}")
        return

    print("=" * 60)
    print(f"🚀 POSTING REEL TO INSTAGRAM (@coool_verse_)")
    print(f"📹 Video: {os.path.basename(reel_path)}")
    print(f"🎯 Hook: {target.get('hook_line1')} / {target.get('hook_line2')}")
    print("=" * 60)

    print("🔐 Authenticating Instagram Client...")
    cl = get_client()
    user_info = cl.account_info()
    print(f"✅ Logged in as: @{user_info.username} (PK: {user_info.pk})")

    # Generate a thumbnail frame
    thumb_path = reel_path.replace(".mp4", "_thumb.jpg")
    ffmpeg_bin = os.getenv("FFMPEG_PATH") or shutil.which("ffmpeg") or "ffmpeg"
    if not os.path.exists(thumb_path):
        cmd = [
            ffmpeg_bin, "-y", "-ss", "00:00:02",
            "-i", reel_path,
            "-vframes", "1",
            thumb_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"📤 Uploading reel to Instagram (Size: {os.path.getsize(reel_path) / (1024*1024):.2f} MB)...")
    try:
        media = cl.clip_upload(
            path=Path(reel_path),
            caption=caption,
            thumbnail=Path(thumb_path) if os.path.exists(thumb_path) else None
        )
        post_code = media.code
        reel_url = f"https://www.instagram.com/reel/{post_code}/"

        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Reel uploaded to Instagram!")
        print(f"🔗 Live Reel URL: {reel_url}")
        print("=" * 60)

        # Update manifest
        target["status"] = "posted"
        target["posted_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        target["instagram_url"] = reel_url
        target["media_id"] = str(media.pk)

        with open(MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)

        # Move in Google Drive
        if drive_id:
            move_in_drive(drive_id, DRIVE_ARCHIVE_ID)

        # Append to Desktop clipping links file if Desktop exists
        desktop_file = Path("/home/vivek/Desktop/preme_clipping_links.txt")
        if desktop_file.parent.exists():
            with open(desktop_file, "a") as df:
                df.write(f"[{time.strftime('%Y-%m-%d %H:%M')}] {target.get('hook_line1')} - {reel_url}\n")
            print(f"📄 Saved link to {desktop_file}")

        return reel_url

    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None

if __name__ == "__main__":
    post_next_reel()
