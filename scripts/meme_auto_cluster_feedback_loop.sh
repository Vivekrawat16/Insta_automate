#!/bin/bash
# 2-Day Algorithmic Feedback Loop & Topic Cluster Pipeline for @vformemes
# 1. Audits Instagram reel performance (views, likes, comments)
# 2. Identifies top performing theme (e.g. chaar log, pg landlord)
# 3. Generates and renders 3 spin-off reels clustered on that theme
# 4. Uploads them to Google Drive queue for automatic cloud posting

set -e
export PATH="/home/vivek/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

BASE_DIR="/home/vivek/nifi/meme_build"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/cluster_loop_$(date +'%Y%m%d').log"
echo "==========================================================" >> "$LOG_FILE"
echo "📈 [$(date +'%Y-%m-%d %H:%M:%S')] Starting @vformemes Topic Clustering Loop..." >> "$LOG_FILE"
echo "==========================================================" >> "$LOG_FILE"

cd "$BASE_DIR"
/home/vivek/nifi/insta_env/bin/python "$BASE_DIR/cluster_pipeline.py" 3 >> "$LOG_FILE" 2>&1

echo "✅ [$(date +'%Y-%m-%d %H:%M:%S')] Topic Clustering Batch Complete!" >> "$LOG_FILE"
