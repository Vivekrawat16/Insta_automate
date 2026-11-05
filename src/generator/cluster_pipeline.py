#!/usr/bin/env python3
"""
Meme Topic Cluster Pipeline for @vformemes
Runs every 2 days to:
1. Audit Instagram performance and find winning topics
2. Generate 3 clustered spin-off reel specifications
3. Render 1080x1920 Option A reels with @vformemes branding
4. Upload to Google Drive queue (15tEG1buRhHi8g4lkv98KMJC_-LHupuvV)
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

from performance_auditor import audit_performance
from cluster_generator import generate_cluster_batch
from render_centered_meme import render_centered_meme

GDRIVE_MEMES_FOLDER_ID = (os.getenv("GDRIVE_FOLDER_ID") or "15tEG1buRhHi8g4lkv98KMJC_-LHupuvV").strip()
GDRIVE_SA_KEY = os.getenv("GDRIVE_SA_KEY", "")
CLUSTER_LOG_FILE = BASE_DIR / "cluster_execution_history.json"
TMP_OUT_DIR = Path("/tmp/meme_cluster_out")

def upload_via_service_account(file_path: str, parent_folder_id: str) -> str:
    """Uploads file using Google Drive API Service Account."""
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
    """Uploads file using gdrive CLI."""
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
    print(f"  ⚠️ No Google Drive upload method available (neither GDRIVE_SA_KEY nor gdrive CLI).")
    return ""

def run_feedback_loop_batch(num_reels: int = 3):
    print("=" * 65)
    print("🚀 RUNNING @vformemes TOPIC CLUSTERING FEEDBACK LOOP")
    print("=" * 65)

    TMP_OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Audit Performance
    try:
        audit_res = audit_performance(limit=15)
        winner = audit_res.get("winner")
        winning_topic = winner["topic"] if winner else "chaar_log_relatives"
        print(f"\n🎯 Targeted Viral Topic: '{winning_topic.upper()}' (Avg Score: {winner.get('avg_score', 'N/A')})")
    except Exception as e:
        print(f"⚠️ Performance audit fallback triggered ({e}). Using 'chaar_log_relatives'.")
        winning_topic = "chaar_log_relatives"

    # 2. Generate Cluster Specs
    print(f"\n🧠 Generating {num_reels} spin-off variations for topic: {winning_topic}...")
    cluster_specs = generate_cluster_batch(winning_topic, count=num_reels)

    results = []
    # 3. Render and Upload each reel
    for i, spec in enumerate(cluster_specs, 1):
        slug = spec["slug"]
        raw_video = spec.get("resolved_video") or spec.get("raw_video")
        out_filename = f"reel_cluster_{int(time.time())}_{slug}.mp4"
        out_path = str(TMP_OUT_DIR / out_filename)

        print(f"\n[{i}/{len(cluster_specs)}] Rendering Clustered Reel: '{slug}'...")
        if not raw_video or not os.path.exists(raw_video):
            print(f"  ❌ Raw character video missing: {raw_video}")
            continue

        render_centered_meme(
            video_in=raw_video,
            lines=spec["lines"],
            output_mp4=out_path,
            duration=spec.get("duration", 6.5),
            aspect=spec.get("aspect", "16:9"),
            watermark="@vformemes",
            ss_offset=spec.get("ss_offset", 0)
        )
        file_size_mb = os.path.getsize(out_path) / (1024 * 1024)
        print(f"  ✅ Rendered successfully: {out_filename} ({file_size_mb:.2f} MB)")

        # Upload to Google Drive Queue
        drive_id = upload_to_drive(out_path, GDRIVE_MEMES_FOLDER_ID)

        results.append({
            "slug": slug,
            "filename": out_filename,
            "drive_id": drive_id,
            "topic": winning_topic,
            "caption": spec.get("caption", ""),
            "rendered_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Save to history
    history = []
    if CLUSTER_LOG_FILE.exists():
        try:
            with open(CLUSTER_LOG_FILE, "r") as fp:
                history = json.load(fp)
        except Exception:
            history = []
    history.append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "winning_topic": winning_topic,
        "batch_count": len(results),
        "reels": results
    })
    with open(CLUSTER_LOG_FILE, "w") as fp:
        json.dump(history, fp, indent=2)

    print("\n" + "=" * 65)
    print(f"🏁 CLUSTER BATCH COMPLETE: {len(results)} themed reels added to Drive Queue!")
    print("=" * 65)

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run_feedback_loop_batch(count)
