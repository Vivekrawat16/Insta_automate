#!/home/vivek/nifi/insta_env/bin/python
import os
import sys
import json
import re
import time
import random
import subprocess
from pathlib import Path
from instagrapi import Client

DRIVE_MEMES_FOLDER_ID = "15tEG1buRhHi8g4lkv98KMJC_-LHupuvV"
DRIVE_ARCHIVE_FOLDER_ID = "19oTHwlAxucPomUfLXAOanyDyzTMeshya"

BASE_DIR = "/home/vivek/nifi"
TMP_DIR = "/tmp/insta_upload"
SESSION_FILE = os.path.join(BASE_DIR, "insta_session.json")
LOG_FILE = os.path.join(BASE_DIR, "instagram_posted_log.json")

# Default trending hashtags
HASHTAGS = "#relatable #desimemes #corporatehumor #indianmemes #memesdaily #dankmemes #trendingreels #explorepage #viralmemes #laughter #adultingishard #comedy #memestagram"

CAPTION_TEMPLATES = {
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
}

def generate_caption(filename):
    # Extract slug
    slug = ""
    m = re.match(r'reel_\d+_(.*?)\.mp4$', filename)
    if m:
        slug = m.group(1)

    intro = CAPTION_TEMPLATES.get(slug, "")
    if not intro:
        # Fallback clean title
        words = slug.replace('_', ' ').title()
        intro = f"{words} 💀😭 Every single time.\n\n"

    return f"{intro}{HASHTAGS}"

def get_pending_reels():
    res = subprocess.run(['gdrive', 'readonly', 'ls', DRIVE_MEMES_FOLDER_ID, '--json'], stdout=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Failed to list Drive files: {res.stderr}", file=sys.stderr)
        return []

    items = json.loads(res.stdout)
    reels = []
    for item in items:
        name = item.get('name', '')
        # Only match reel_*.mp4 files, skip folders
        m = re.match(r'reel_(\d+)_.*\.mp4$', name)
        if m:
            num = int(m.group(1))
            reels.append({
                'id': item.get('id'),
                'name': name,
                'num': num,
                'size': item.get('size', 0)
            })

    # Sort in ascending order by reel number (oldest/first created first)
    reels.sort(key=lambda x: x['num'])
    return reels

def load_instagram_client():
    if not os.path.exists(SESSION_FILE):
        raise FileNotFoundError(f"Session file not found at {SESSION_FILE}. Run login first.")

    cl = Client()
    cl.load_settings(SESSION_FILE)
    cl.delay_range = [2, 5]
    print(f"Loaded Instagram session for user ID: {cl.user_id}")
    return cl

def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Instagram Reel Posting Automation...")
    os.makedirs(TMP_DIR, exist_ok=True)

    # 1. Fetch pending reels from Google Drive
    pending = get_pending_reels()
    print(f"Found {len(pending)} pending reels in Drive folder.")

    if not pending:
        print("No pending reels found in Google Drive folder! Everything is posted.")
        return

    # Pick the next reel in line
    next_reel = pending[0]
    reel_id = next_reel['id']
    reel_name = next_reel['name']
    reel_num = next_reel['num']

    print(f"\nNext reel to post: #{reel_num} -> {reel_name} (ID: {reel_id})")

    # 2. Check local path or download from Drive
    local_path = os.path.join(TMP_DIR, reel_name)
    print(f"Downloading {reel_name} from Google Drive...")
    dl_res = subprocess.run(['gdrive', 'readonly', 'download', reel_id, '--out', local_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if dl_res.returncode != 0 or not os.path.exists(local_path):
        print(f"Error downloading reel: {dl_res.stderr}", file=sys.stderr)
        return

    file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"Downloaded reel successfully ({file_size_mb:.2f} MB)")

    # 3. Generate Caption
    caption = generate_caption(reel_name)
    print(f"\nCaption generated:\n---\n{caption}\n---")

    # 4. Generate Thumbnail
    thumb_path = local_path + ".jpg"
    print(f"Generating thumbnail via ffmpeg: {thumb_path}")
    subprocess.run([
        '/home/vivek/nifi/meme_build/ffmpeg', '-y',
        '-ss', '00:00:01',
        '-i', local_path,
        '-vframes', '1',
        thumb_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 5. Connect to Instagram and Upload
    cl = load_instagram_client()

    # Pre-upload human-like delay
    pause_sec = random.randint(10, 18)
    print(f"Simulating human pause ({pause_sec}s) before posting...")
    time.sleep(pause_sec)

    print("Uploading Reel to Instagram via instagrapi...")
    media = cl.clip_upload(
        path=Path(local_path),
        caption=caption,
        thumbnail=Path(thumb_path) if os.path.exists(thumb_path) else None
    )

    insta_url = f"https://www.instagram.com/reel/{media.code}/"
    print(f"\n🎉 REEL POSTED SUCCESSFULLY TO INSTAGRAM!")
    print(f"Instagram Post URL: {insta_url}")
    print(f"Media PK: {media.pk}")

    # 5. Move Reel in Google Drive to Uploaded_Archive
    print(f"\nMoving {reel_name} to Uploaded_Archive folder in Google Drive...")
    mv_res = subprocess.run(['gdrive', 'mutate', 'mv', reel_id, DRIVE_ARCHIVE_FOLDER_ID], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if mv_res.returncode == 0:
        print(f"Moved to Uploaded_Archive successfully!")
    else:
        print(f"Warning: Failed to move in Drive: {mv_res.stderr}", file=sys.stderr)

    # 6. Save Log Entry
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        except Exception:
            logs = []

    logs.append({
        'reel_num': reel_num,
        'filename': reel_name,
        'drive_id': reel_id,
        'insta_code': media.code,
        'insta_url': insta_url,
        'posted_at': time.strftime('%Y-%m-%d %H:%M:%S')
    })

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

    # 7. Cleanup local tmp file
    try:
        if os.path.exists(local_path):
            os.remove(local_path)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    except Exception:
        pass

    # Save updated session settings
    cl.dump_settings(SESSION_FILE)
    print(f"\nExecution finished! Posted reel logged in {LOG_FILE}.")

if __name__ == '__main__':
    main()
