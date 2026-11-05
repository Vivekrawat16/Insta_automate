#!/bin/bash
# Preme Clipping Daily Automation Script
# Runs automated pipeline: Fetch clips -> Generate Hooks -> Render 1080x1920 -> Upload to Drive

set -e
export PATH="/home/vivek/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

BASE_DIR="/home/vivek/preme_clipping"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/daily_pipeline_$(date +'%Y%m%d').log"
echo "==========================================================" >> "$LOG_FILE"
echo "🚀 [$(date +'%Y-%m-%d %H:%M:%S')] Starting Preme Clipping Batch..." >> "$LOG_FILE"
echo "==========================================================" >> "$LOG_FILE"

cd "$BASE_DIR"
/usr/bin/python3 "$BASE_DIR/pipeline.py" 3 >> "$LOG_FILE" 2>&1

echo "✅ [$(date +'%Y-%m-%d %H:%M:%S')] Preme Batch Finished!" >> "$LOG_FILE"
