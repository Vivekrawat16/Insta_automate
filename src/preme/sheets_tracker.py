#!/usr/bin/env python3
"""
Preme Clipping Google Sheet Live Tracker
Maintains live ledger of all posted reels on @coool_verse_ for campaign bounty tracking.
Works in:
1. Cloud GitHub Actions (using Service Account via GDRIVE_SA_KEY)
2. Local System (using gsheets CLI or fallback)
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime

PREME_TRACKER_SPREADSHEET_ID = (
    os.getenv("PREME_TRACKER_SPREADSHEET_ID") or "15L1lGAcGK-WVJN9Jp-MwimjwszsUF-Hiog4PhOgRHIk"
).strip()
GDRIVE_SA_KEY = os.getenv("GDRIVE_SA_KEY", "")

def append_via_sheets_api(spreadsheet_id: str, row: list) -> bool:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        sa_info = json.loads(GDRIVE_SA_KEY)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        service = build("sheets", "v4", credentials=creds)
        body = {"values": [row]}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        print(f"  📊 [Google Sheet API] Successfully appended row to Tracker Sheet!")
        return True
    except Exception as e:
        print(f"  ❌ Google Sheets API append error: {e}")
        return False

def append_via_gsheets_cli(spreadsheet_id: str, row: list) -> bool:
    gsheets_bin = shutil.which("gsheets") or "/home/vivek/.gemini/antigravity/bin/gsheets"
    if not os.path.exists(gsheets_bin) and not shutil.which("gsheets"):
        return False

    escaped_row = [str(cell).replace(",", "\\,").replace('"', '\"') for cell in row]
    row_str = ",".join(escaped_row)

    cmd = [gsheets_bin, "mutate", "append", spreadsheet_id, "Sheet1", row_str]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print(f"  📊 [gsheets CLI] Successfully appended row to Tracker Sheet!")
        return True
    else:
        print(f"  ❌ gsheets CLI error: {res.stderr}")
        return False

def record_posted_reel_to_sheet(
    reel_url: str,
    hook_title: str,
    twitch_url: str = "",
    duration: float = 14.0,
    media_pk: str = "",
    status: str = "TRACKING",
    posted_at: str = None
) -> bool:
    """
    Appends a new reel record to the Preme Clipping Tracker Google Sheet.
    """
    if not posted_at:
        posted_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    row = [
        posted_at,
        hook_title,
        reel_url,
        twitch_url,
        str(duration),
        status,
        str(media_pk)
    ]

    print(f"\n📊 Recording live reel to Google Sheet: {PREME_TRACKER_SPREADSHEET_ID}...")
    if GDRIVE_SA_KEY:
        ok = append_via_sheets_api(PREME_TRACKER_SPREADSHEET_ID, row)
        if ok:
            return True

    return append_via_gsheets_cli(PREME_TRACKER_SPREADSHEET_ID, row)

if __name__ == "__main__":
    record_posted_reel_to_sheet(
        reel_url="https://www.instagram.com/reel/TEST/",
        hook_title="TEST HOOK TITLE",
        twitch_url="https://twitch.tv/test",
        duration=14.0,
        media_pk="999999999"
    )
