#!/usr/bin/env python3
"""
Cloud Instagram Reel Poster
Runs headless on GitHub Actions (or locally) to:
1. Fetch the next pending reel from Google Drive via Service Account
2. Generate thumbnail and caption
3. Upload to Instagram via instagrapi (Reel feed upload only)
4. Move reel to Uploaded_Archive folder in Google Drive
"""

import os
import sys
import io
import json
import re
import time
import shutil
import random
import subprocess
import urllib.parse
from pathlib import Path
import requests

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Google Drive API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Instagram API
from instagrapi import Client

# Configuration via Environment Variables with sensible defaults
GDRIVE_FOLDER_ID = (os.getenv("GDRIVE_FOLDER_ID") or "15tEG1buRhHi8g4lkv98KMJC_-LHupuvV").strip()
GDRIVE_ARCHIVE_ID = (os.getenv("GDRIVE_ARCHIVE_ID") or "19oTHwlAxucPomUfLXAOanyDyzTMeshya").strip()
GDRIVE_SA_KEY = os.getenv("GDRIVE_SA_KEY", "")

INSTA_SESSION_JSON = os.getenv("INSTA_SESSION_JSON", "")
PROXY_URL = os.getenv("PROXY_URL", "").strip()

TMP_DIR = "/tmp/insta_cloud_upload"

HASHTAGS = "#relatable #desimemes #corporatehumor #indianmemes #memesdaily #dankmemes #trendingreels #explorepage #viralmemes #laughter #adultingishard #comedy #memestagram"

CAPTION_TEMPLATES = {
    "exam_panic": "Exam in 5 hours, haven't opened the book, 5 units syllabus aur haath me thandi chai 💀😭 Accepting god's plan at this point.\n\nTag that backbencher friend who survives on one-night study! 😂\n\n",
    "corporate_spine": "L-shaped posture at 4 PM vs Ergonomic chair promises 💀😭 Spine has officially left the chat.\n\n",
    "bumble_trauma": "Dating apps in 2026: Ghosting after 3 days of deep soul connection 💀😭 Modern romance.\n\n",
    "hr_pizza_party": "Appraisal hike: 0.5% budget constraint. Meanwhile HR: Free pizza party guys! 💀😭 Corporate solutions.\n\n",
    "zepto_free_gift": "Order ₹199 ka free gift lene ke liye ₹1500 ki cart bana li 💀😭 Peak financial intellect.\n\n",
    "desi_ghee_diet": "Calorie count planning vs Mummy ka unconditional desi ghee 💀😭 Baat khatam.\n\nTag that gym bro who can relate! 😂\n\n",
    "weekend_manager_sync": "Friday 6 PM ka 'Enjoy Weekend' vs Saturday 8 AM ka 'Quick Sync' 💀😭\n\nCorporate majdoori at its finest.\n\n",
    "linkedin_influencer_ant": "Ant hustle mentality se multi-million dollar lessons 💀😭 LinkedIn influencers need to be stopped.\n\n",
    "sip_smallcap_crash": "Small Cap SIP wealth creation vs Nifty 500-point dip 💀😭 Timing is everything.\n\n",
    "landlord_security_deposit": "Air wear-and-tear aur negative vibe deduction 💀😭 Bangalore landlord supremacy.\n\n",
    "ai_replaces_devs": "Coding seekho beta scope hai 💀😭 2 mahine baad intern + AI ne replace kar diya.\n\n",
    "blinkit_vs_life": "Blinkit 7 min me aa jata hai, par 1 text ka reply karne me 4 ghante 💀😭 Overthinking peak.\n\n",
    "startup_pitch_relatives": "Beta company me karte kya ho exact batao 💀😭 Chief Growth Hacker in stealth mode.\n\n",
    "doctor_chemist_handwriting": "Doctor ki hieroglyphics vs Chemist bhaiya ka superpower 💀😭 Without looking 3 strips de diya.\n\n",
    "3am_motivation_trap": "3 AM startup plans vs 8:30 AM snooze button 💀😭 Every single night story.\n\n",
    "notice_period_prison": "3 months notice period: Staring at the ceiling while knowledge transfer file sits empty 💀😭 Jail release count chal raha hai.\n\n",
    "royal_dansk_sewing_kit": "Butter cookies ka dabba khola, andar se dhaga aur sui nikli 💀😭 Universal Indian household betrayal.\n\n",
    "seventy_hour_workweek": "70 hours workweek debate vs 2 ghante lunch break aur chai tapri discussions 💀😭 Balance maintain hona chahiye.\n\n",
    "irctc_tatkal_bossfight": "10:00 AM Tatkal window open: Captcha solved in 0.2s, bank OTP arrives at 10:15 AM 💀😭 Waiting list 150.\n\n",
    "gym_protein_contraband": "Protein powder ka dabba chupana vs Mummy asking ye dabba kiska hai 💀😭 Supplements explaining nightmare.\n\n",
    "upi_chai_tapri_stare": "Server down on UPI: Bhaiya code scan kiya hai wait karo gpay circle ghoom raha hai 💀😭 Most awkward 30 seconds of life.\n\n",
    "bangalore_orr_rto_traffic": "Silk Board se Marathahalli: Distance 8 km, Travel time 2 business days 💀😭 Fuel gauge dropping, hope leaving body.\n\n",
    "shaadi_fufaji_critique": "Gulab jamun garam nahi tha aur paneer hard tha 💀😭 Fufaji review on point.\n\n",
    "prod_hotfix_diwali_oncall": "Diwali evening, patakhe phoot rahe hain aur production server 500 error throw kar raha hai 💀😭 PagerDuty ringtone trauma.\n\n",
}

PREME_HASHTAGS = "#preme #kickstreamer #streamer #twitchclips #irlstream #viralmoments #clipping #fyp #explorepage"

PREME_CAPTIONS_POOL = [
    "Wait till the end... This stream moment was wild 💀😭\n\nTag a friend who needs to see this! 👇\n\n{tags}",
    "Nah Preme actually had zero filter on stream 💀😭 How did he say that?\n\nFollow for daily clips! 👇\n\n{tags}",
    "Bro thought nobody was recording this 💀😭 Pure stream comedy.\n\nDrop a comment if you saw this live! 👇\n\n{tags}",
    "Preme's reaction at the end was completely unhinged 💀😭 You can't make this up.\n\nTag that one friend 👇\n\n{tags}",
    "The way he said that with a straight face 💀😭 Absolutely legendary stream moment.\n\nSave this for later! 👇\n\n{tags}",
    "I was not expecting him to do that 💀😭 Caught in 4k on stream.\n\nShare this with someone who watches Preme! 👇\n\n{tags}",
    "Streamers when the intrusive thoughts win 💀😭 Preme is unreal.\n\nFollow @coool_verse_ for more! 👇\n\n{tags}",
    "This might be the most chaotic moment on Kick this week 💀😭 Watch till the end.\n\nDrop a 💀 in the comments! 👇\n\n{tags}",
]

def generate_caption(filename):
    if filename.startswith("preme_reel_"):
        template = random.choice(PREME_CAPTIONS_POOL)
        return template.format(tags=PREME_HASHTAGS)

    slug = ""
    m = re.match(r'reel_\d+_(.*?)\.mp4$', filename)
    if m:
        slug = m.group(1)

    intro = CAPTION_TEMPLATES.get(slug, "")
    if not intro:
        words = slug.replace('_', ' ').title()
        intro = f"{words} 💀😭 Every single time.\n\n"

    return f"{intro}{HASHTAGS}"

def get_drive_service():
    """Initializes Google Drive v3 API client using Service Account."""
    if not GDRIVE_SA_KEY:
        raise ValueError("GDRIVE_SA_KEY environment variable is missing! Provide the Google Service Account JSON.")

    if os.path.exists(GDRIVE_SA_KEY):
        with open(GDRIVE_SA_KEY, "r") as f:
            sa_info = json.load(f)
    else:
        try:
            sa_info = json.loads(GDRIVE_SA_KEY)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse GDRIVE_SA_KEY as JSON: {e}")

    creds = service_account.Credentials.from_service_account_info(
        sa_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def fetch_pending_reels(drive_service):
    """Lists and sorts pending reel MP4s from Google Drive queue folder."""
    print(f"Scanning Google Drive queue folder: '{GDRIVE_FOLDER_ID}'...")
    query = f"'{GDRIVE_FOLDER_ID}' in parents and mimeType='video/mp4' and trashed=false"
    results = drive_service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, size, createdTime)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = results.get("files", [])
    print(f"Total MP4 files discovered in Drive queue folder: {len(files)}")
    reels = []
    for item in files:
        name = item.get("name", "")
        if not name.endswith(".mp4"):
            continue

        m_meme = re.match(r'reel_(\d+)_.*\.mp4$', name)
        m_preme = re.match(r'preme_reel_(\d+)\.mp4$', name)

        if m_meme:
            reels.append({
                "id": item.get("id"),
                "name": name,
                "num": int(m_meme.group(1)),
                "size": int(item.get("size", 0)),
                "createdTime": item.get("createdTime", "")
            })
        elif m_preme:
            reels.append({
                "id": item.get("id"),
                "name": name,
                "num": int(m_preme.group(1)),
                "size": int(item.get("size", 0)),
                "createdTime": item.get("createdTime", "")
            })
        else:
            reels.append({
                "id": item.get("id"),
                "name": name,
                "num": 999999,
                "size": int(item.get("size", 0)),
                "createdTime": item.get("createdTime", "")
            })

    # For Preme queue, sort FIFO by createdTime (oldest first); For memes, sort by numeric reel sequence
    if GDRIVE_FOLDER_ID == "1NuU7Jc3zLVnd08UZh6U-2QrlWxOmEWXr" or (reels and reels[0]["name"].startswith("preme_reel_")):
        reels.sort(key=lambda x: x.get("createdTime", ""))
    else:
        reels.sort(key=lambda x: (x["num"], x.get("createdTime", "")))

    return reels

def download_file_from_drive(drive_service, file_id, destination_path):
    """Downloads a file from Google Drive using streaming chunks."""
    request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
    with io.FileIO(destination_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024 * 2)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                percent = int(status.progress() * 100)
                sys.stdout.write(f"\rDownloading from Drive: {percent}%")
                sys.stdout.flush()
    print("\nDownload complete.")

def move_drive_file(drive_service, file_id):
    """Moves processed reel from queue folder to archive folder in Google Drive."""
    try:
        drive_service.files().update(
            fileId=file_id,
            addParents=GDRIVE_ARCHIVE_ID,
            removeParents=GDRIVE_FOLDER_ID,
            supportsAllDrives=True,
            fields="id, parents"
        ).execute()
        print(f"✅ Successfully moved reel {file_id} to Uploaded_Archive in Google Drive.")
        return True
    except Exception as e:
        print(f"⚠️ Warning: Could not move file in Drive: {e}", file=sys.stderr)
        return False

def init_instagram_client():
    """Initializes instagrapi Client with session settings and optional proxy."""
    if not INSTA_SESSION_JSON:
        raise ValueError("INSTA_SESSION_JSON environment variable is missing! Provide the Instagram session JSON.")

    cl = Client()
    cl.delay_range = [2, 5]

    if PROXY_URL:
        print(f"🌐 Setting proxy: {PROXY_URL}")
        cl.set_proxy(PROXY_URL)

    session_path = os.path.join(TMP_DIR, "session_active.json")
    if os.path.exists(INSTA_SESSION_JSON):
        cl.load_settings(INSTA_SESSION_JSON)
    else:
        try:
            session_data = json.loads(INSTA_SESSION_JSON)
            with open(session_path, "w") as f:
                json.dump(session_data, f)
            cl.load_settings(session_path)
        except Exception as e:
            raise ValueError(f"Failed to load INSTA_SESSION_JSON: {e}")

    # Verify session validity
    try:
        user_info = cl.account_info()
        print(f"✅ Authenticated as Instagram User: @{user_info.username} (PK: {user_info.pk})")
    except Exception as e:
        raise RuntimeError(f"Instagram session authentication failed: {e}")

    return cl

def send_whatsapp_alert(reel_num, filename, insta_url, remaining_count=None):
    """Sends free WhatsApp alert via CallMeBot gateway if configured."""
    phone = os.getenv("WHATSAPP_PHONE", "").strip()
    apikey = os.getenv("WHATSAPP_APIKEY", "").strip()

    if not phone or not apikey:
        print("ℹ️ WhatsApp alerts disabled (WHATSAPP_PHONE or WHATSAPP_APIKEY secret not configured).")
        return

    # Clean display topic
    slug = filename.replace(".mp4", "")
    m = re.match(r'reel_\d+_(.*)', slug)
    topic = m.group(1).replace('_', ' ').title() if m else slug

    account_name = "@coool_verse_" if ("preme" in filename.lower() or GDRIVE_FOLDER_ID == "1NuU7Jc3zLVnd08UZh6U-2QrlWxOmEWXr") else "@vformemes"
    msg = f"🎉 *Reel Live on Instagram!*\n\n🎬 *Account:* {account_name}\n📌 *Topic:* {topic}\n🔗 *Link:* {insta_url}"
    if remaining_count is not None:
        msg += f"\n📦 *Queue Remaining:* {remaining_count} reels"

    try:
        encoded_text = urllib.parse.quote_plus(msg)
        # CallMeBot WhatsApp API Gateway
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_text}&apikey={apikey}"
        resp = requests.get(url, timeout=12)
        if resp.status_code == 200:
            print("📱 WhatsApp alert sent successfully!")
        else:
            print(f"⚠️ WhatsApp alert response: HTTP {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to send WhatsApp alert: {e}")

def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Starting Cloud Instagram Reel Poster...")
    os.makedirs(TMP_DIR, exist_ok=True)

    # 1. Initialize Drive API
    print("Connecting to Google Drive API via Service Account...")
    drive_service = get_drive_service()

    # 2. Get Pending Reels
    pending = fetch_pending_reels(drive_service)
    print(f"Found {len(pending)} pending reels in Google Drive queue.")

    if not pending:
        print("🎉 No pending reels in Google Drive queue! All reels have been posted.")
        sys.exit(0)

    next_reel = pending[0]
    reel_id = next_reel["id"]
    reel_name = next_reel["name"]
    reel_num = next_reel["num"]

    print(f"\n🎯 Next reel in queue: #{reel_num} -> {reel_name} (ID: {reel_id})")

    # 3. Download from Google Drive
    local_path = os.path.join(TMP_DIR, reel_name)
    download_file_from_drive(drive_service, reel_id, local_path)
    file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"Downloaded reel size: {file_size_mb:.2f} MB")

    # 4. Generate Caption
    caption = generate_caption(reel_name)
    print(f"\nGenerated Caption:\n---\n{caption}\n---")

    # 5. Generate Thumbnail (via FFmpeg if available, else Instagram auto-generates)
    thumb_path = local_path + ".jpg"
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    try:
        subprocess.run([
            ffmpeg_bin, "-y",
            "-ss", "00:00:01",
            "-i", local_path,
            "-vframes", "1",
            thumb_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except Exception as te:
        print(f"ℹ️ Custom thumbnail skipped ({te}); Instagram will generate thumbnail from frame 1.")

    # 6. Initialize Instagram Client
    print("\nConnecting to Instagram...")
    cl = init_instagram_client()

    # Pre-upload human-like pause
    pause_sec = random.randint(10, 18)
    print(f"Simulating human pause ({pause_sec}s) before posting...")
    time.sleep(pause_sec)

    # 7. Upload Reel
    print(f"Uploading Reel '{reel_name}' to Instagram...")
    media = cl.clip_upload(
        path=Path(local_path),
        caption=caption,
        thumbnail=Path(thumb_path) if os.path.exists(thumb_path) else None
    )

    insta_url = f"https://www.instagram.com/reel/{media.code}/"
    print(f"\n🎉 REEL POSTED SUCCESSFULLY TO INSTAGRAM!")
    print(f"Instagram Post URL: {insta_url}")
    print(f"Media PK: {media.pk}")

    # 7b. If this is a Preme Campaign Reel, Record to Google Sheet Tracker
    if "preme" in reel_name.lower() or GDRIVE_FOLDER_ID == "1NuU7Jc3zLVnd08UZh6U-2QrlWxOmEWXr":
        try:
            try:
                from src.preme.sheets_tracker import record_posted_reel_to_sheet
            except ImportError:
                from sheets_tracker import record_posted_reel_to_sheet

            record_posted_reel_to_sheet(
                reel_url=insta_url,
                hook_title=caption.split('\n')[0][:80] if caption else reel_name,
                duration=14.0,
                media_pk=str(media.pk),
                status="TRACKING"
            )
        except Exception as se:
            print(f"⚠️ Warning: Could not log Preme reel to Google Sheet: {se}")

    # 8. Move Reel to Uploaded_Archive in Google Drive
    print(f"\nArchiving reel in Google Drive...")
    move_drive_file(drive_service, reel_id)

    # 10. Send Free WhatsApp Alert (if secrets configured)
    remaining_count = max(0, len(pending) - 1)
    send_whatsapp_alert(reel_num, reel_name, insta_url, remaining_count=remaining_count)

    # 11. Clean up temporary files
    for p in (local_path, thumb_path):
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ Cloud Pipeline Complete!")

if __name__ == "__main__":
    main()
