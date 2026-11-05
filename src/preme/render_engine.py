#!/usr/bin/env python3
"""
Preme Reel Render Engine
Composites raw stream clips into 9:16 Instagram Reels (1080x1920):
- Background: Blurred & darkened video stream
- Center: 16:9 stream clip (1080x608)
- Top: 2-line high-contrast hook headline banner
- Bottom: Centered official Preme Overlay (logo + badges)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OVERLAY_PNG = str(BASE_DIR / "assets" / "Preme_Overlay.png")

# Auto-detect FFmpeg
FFMPEG_BIN = os.getenv("FFMPEG_PATH") or shutil.which("ffmpeg") or "ffmpeg"

# Fonts
FONT_DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONTSERRAT = str(BASE_DIR.parent / "generator" / "assets" / "Montserrat-Bold.ttf")
FONT_PATH = FONT_MONTSERRAT if os.path.exists(FONT_MONTSERRAT) else FONT_DEJAVU

def escape_drawtext(text: str) -> str:
    """Escapes special characters for FFmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "'\\''")
    text = text.replace(":", "\\:")
    text = text.replace(",", "\\,")
    text = text.replace("$", "\\$")
    text = text.replace("%", "\\%")
    return text

def render_preme_reel(
    input_video: str,
    output_mp4: str,
    hook_line1: str,
    hook_line2: str = "",
    start_time: float = 0,
    duration: float = None,
    max_duration: float = 15.0
) -> bool:
    """
    Renders a 1080x1920 Reel matching the approved Preme campaign aesthetic.
    Restricted to max_duration (default 15.0s max) for high audience retention.
    """
    if not os.path.exists(input_video):
        print(f"Error: Input video not found at {input_video}")
        return False

    if not os.path.exists(OVERLAY_PNG):
        print(f"Error: Preme overlay not found at {OVERLAY_PNG}")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)

    # Cap duration to max 15.0 seconds
    target_duration = max_duration
    if duration and duration < max_duration:
        target_duration = duration

    fade_start = max(0.5, target_duration - 1.2)

    esc_h1 = escape_drawtext(hook_line1.upper())
    esc_h2 = escape_drawtext(hook_line2.upper()) if hook_line2 else ""

    font_arg = f":fontfile='{FONT_PATH}'" if os.path.exists(FONT_PATH) else ""

    # Text filter
    if esc_h2:
        text_filters = (
            f"drawtext=text='{esc_h1}'{font_arg}:fontsize=44:fontcolor=white:"
            f"box=1:boxcolor=black@0.75:boxborderw=14:x=(w-text_w)/2:y=420,"
            f"drawtext=text='{esc_h2}'{font_arg}:fontsize=44:fontcolor=yellow:"
            f"box=1:boxcolor=black@0.75:boxborderw=14:x=(w-text_w)/2:y=486"
        )
    else:
        text_filters = (
            f"drawtext=text='{esc_h1}'{font_arg}:fontsize=46:fontcolor=white:"
            f"box=1:boxcolor=black@0.75:boxborderw=16:x=(w-text_w)/2:y=450"
        )

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=35,colorlevels=rimin=0.2:gimin=0.2:bimin=0.2[bg];"
        f"[0:v]scale=1080:608:force_original_aspect_ratio=increase,crop=1080:608,format=yuv420p[center_vid];"
        f"[bg][center_vid]overlay=0:656[comp1];"
        f"[comp1]{text_filters}[comp2];"
        f"[1:v]scale=1080:1920[overlay];"
        f"[comp2][overlay]overlay=0:0[vfinal];"
        f"[0:a]atrim=0:{target_duration},afade=t=out:st={fade_start}:d=1.2[afinal]"
    )

    cmd = [FFMPEG_BIN, "-y"]
    if start_time > 0:
        cmd.extend(["-ss", str(start_time)])

    cmd.extend([
        "-i", input_video,
        "-i", OVERLAY_PNG,
        "-t", str(target_duration),
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4
    ])

    print(f"🎬 Rendering 1080x1920 Preme Reel ({target_duration:.1f}s max): {os.path.basename(output_mp4)}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ FFmpeg error: {res.stderr}")
        return False

    size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"✅ Rendered successfully: {output_mp4} ({size_mb:.2f} MB)")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 3:
        render_preme_reel(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Usage: python render_engine.py <input.mp4> <output.mp4> <hook1> [hook2]")
