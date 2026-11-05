#!/usr/bin/env python3
"""
Preme Twitch & Kick Clip Fetcher
Scrapes high-performing clips and downloads them for processing.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent
MANIFEST_FILE = BASE_DIR / "processed_clips.json"

# Auto-detect yt-dlp
YTDLP_BIN = shutil.which("yt-dlp") or shutil.which("/home/vivek/.local/bin/yt-dlp") or "yt-dlp"

def load_processed_ids() -> set:
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r") as f:
                data = json.load(f)
                return set(data.keys())
        except Exception:
            return set()
    return set()

def save_processed_clip(clip_id: str, meta: dict):
    data = {}
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[clip_id] = meta
    with open(MANIFEST_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fetch_top_twitch_clips(limit: int = 10, time_range: str = "all") -> List[Dict]:
    """
    Scrapes Twitch clips sorted by view count.
    """
    url = f"https://www.twitch.tv/preme/clips?range={time_range}"
    cmd = [
        YTDLP_BIN,
        "--flat-playlist",
        "--dump-json",
        url
    ]
    print(f"🔍 Scraping Twitch clips for Preme ({time_range})...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ yt-dlp error: {res.stderr}")
        return []

    processed = load_processed_ids()
    clips = []
    for line in res.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            cid = str(data.get("id"))
            if cid in processed:
                continue
            clips.append({
                "id": cid,
                "title": data.get("title", ""),
                "url": data.get("url") or f"https://clips.twitch.tv/{cid}",
                "views": data.get("view_count", 0) or 0,
                "duration": data.get("duration", 0) or 0
            })
        except Exception:
            pass

    # Sort descending by views
    clips.sort(key=lambda x: x["views"], reverse=True)
    return clips[:limit]

def download_clip(clip_meta: Dict, output_dir: Path = None) -> str:
    """Downloads clip via yt-dlp."""
    if output_dir is None:
        output_dir = BASE_DIR / "raw_clips"
    output_dir.mkdir(parents=True, exist_ok=True)

    out_tmpl = str(output_dir / f"clip_{clip_meta['id']}.%(ext)s")
    cmd = [
        YTDLP_BIN,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", out_tmpl,
        clip_meta["url"]
    ]
    print(f"⬇️ Downloading clip #{clip_meta['id']}: '{clip_meta['title']}'...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    target_mp4 = str(output_dir / f"clip_{clip_meta['id']}.mp4")
    if os.path.exists(target_mp4):
        return target_mp4
    for f in output_dir.glob(f"clip_{clip_meta['id']}.*"):
        return str(f)
    return ""

if __name__ == "__main__":
    top = fetch_top_twitch_clips(limit=3)
    for c in top:
        print(f"- {c['id']}: {c['title']} ({c['views']} views)")
