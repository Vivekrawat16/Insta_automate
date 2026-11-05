#!/bin/bash
# Preme Clipping Daily Poster Script
# Uploads next pending reel to Instagram (@coool_verse_) and saves URL to Desktop/preme_clipping_links.txt

set -e
export PATH="/home/vivek/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

BASE_DIR="/home/vivek/preme_clipping"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/daily_poster_$(date +'%Y%m%d').log"
echo "==========================================================" >> "$LOG_FILE"
echo "📤 [$(date +'%Y-%m-%d %H:%M:%S')] Starting Preme Instagram Post..." >> "$LOG_FILE"
echo "==========================================================" >> "$LOG_FILE"

cd "$BASE_DIR"
/home/vivek/nifi/insta_env/bin/python "$BASE_DIR/post_next_preme_reel.py" >> "$LOG_FILE" 2>&1

echo "✅ [$(date +'%Y-%m-%d %H:%M:%S')] Preme Post Finished!" >> "$LOG_FILE"
