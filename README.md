# 🤖 Instagram & Content Automation Engine (`Insta_automate`)

Automated end-to-end pipeline for **AI Meme Generation, Video Rendering, Google Drive Cloud Queuing, and Instagram Reels Auto-Publishing**.

---

## 🏗️ Architecture & Pipeline Flow

```
[1. Content Generation Engine]
   Reddit Trending Topics (r/IndianDankMemes, r/indiameme, etc.)
                │
                ▼
   Pillow + FFmpeg Video Composer (1080x1920 9:16 Vertical Reels)
   (White Card + Montserrat-Bold + Apple Skull Emoji + Audio Sync)
                │
                ▼
[2. Google Drive Central Queue]
   Uploads 10 reels daily to Main Queue Folder
                │
                ▼
[3. Drip Reel Publisher (Twice Daily)]
   Cron Schedule: 1:30 PM & 8:30 PM (Asia/Kolkata)
                │
                ├─► Pick next pending reel from Google Drive
                ├─► Auto-generate viral caption + 13 hashtags
                ├─► Natural human pause (10-18s) to avoid bot detection
                ├─► Publish Reel to Instagram via instagrapi
                │
                ▼
[4. Auto-Archive in Google Drive]
   Move uploaded reel to 'Uploaded_Archive' folder (Zero duplicates)
```

---

## 📁 Repository Structure

```
Insta_automate/
├── README.md
├── requirements.txt
├── config.example.json
├── sidecars/                                  # Antigravity scheduled automation configs
│   ├── daily-meme-reels-generator.json        # 12:00 PM generator sidecar
│   ├── instagram-reels-daily-poster.json      # 1:30 PM & 8:30 PM reel poster sidecar
│   └── sync-chats-brain-to-gdrive.json        # Hourly brain & chat backup sidecar
└── src/
    ├── generator/                             # Meme reel rendering engine
    │   ├── render_and_upload_batch.py         # Batch renderer + Drive uploader
    │   ├── specs_template.json                # Structured meme specs format
    │   └── assets/                            # Fonts and overlay images
    │       ├── Montserrat-Bold.ttf
    │       ├── apple_skull.png
    │       └── skull.png
    ├── instagram/                             # Instagram publisher
    │   └── post_next_reel_to_insta.py         # Queue picker, publisher, and archiver
    └── sync/                                  # Cloud workspace & chat backup
        └── sync_brain_chats_to_gdrive.py      # Incremental chat & brain sync script
```

---

## 🚀 Quick Setup & Installation

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/Vivekrawat16/Insta_automate.git
cd Insta_automate

# Create virtual environment and install dependencies
uv venv insta_env
source insta_env/bin/activate
uv pip install -r requirements.txt
```

### 2. Configure Instagram Session (`sessionid`)

To ensure **100% zero password sharing** and avoid 2FA/bot checkpoint triggers:
1. Open Instagram in your browser (Firefox / Chrome).
2. Press `F12` -> Go to **Storage** (or **Application** in Chrome) -> **Cookies** -> `https://www.instagram.com`.
3. Copy the value of the `sessionid` cookie.
4. Run the one-time session generator:

```python
from instagrapi import Client
import urllib.parse

cl = Client()
cl.login_by_sessionid(urllib.parse.unquote("YOUR_SESSION_ID"))
cl.dump_settings("insta_session.json")
print("Session saved successfully!")
```

---

## ⚙️ Running Manually

### Generate & Upload 10 Meme Reels
```bash
python3 src/generator/render_and_upload_batch.py src/generator/specs_template.json
```

### Post Next Reel to Instagram & Move to Archive
```bash
./insta_env/bin/python src/instagram/post_next_reel_to_insta.py
```

### Backup Workspace & Chats to Google Drive
```bash
python3 src/sync/sync_brain_chats_to_gdrive.py
```

---

## ⏰ Scheduled Automations

| Task Name | Schedule | Script Path | Action |
| :--- | :--- | :--- | :--- |
| **Meme Generator** | Daily at **12:00 PM** | `src/generator/render_and_upload_batch.py` | Renders 10 reels and uploads to Drive queue. |
| **Reel Auto-Poster** | Daily at **1:30 PM & 8:30 PM** | `src/instagram/post_next_reel_to_insta.py` | Posts next reel to Instagram & moves to Archive. |
| **Chat & Brain Sync** | Hourly at **minute 30** | `src/sync/sync_brain_chats_to_gdrive.py` | Incremental chat backup to Google Drive. |

---

## 🛡️ Account Safety Architecture

- **Residential IP:** Runs on your local broadband connection; Instagram never sees a suspicious cloud datacenter IP.
- **Session Persistence:** Avoids repeated username/password logins by loading `insta_session.json`.
- **Drip Posting:** Posts only 2 reels per day spaced 7 hours apart, perfectly matching human usage.
- **Randomized Jitter:** Waits 10–18 seconds between internal actions with dynamic delay intervals.

---

## 📄 License
MIT License. Built for automated content operations.
