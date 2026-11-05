#!/usr/bin/env python3
"""
Centered Dark Theme Meme Reel Renderer (Option A)
Renders viral 1080x1920 Instagram Reels with:
- Pure black canvas
- Eye-level optical center ratio (no empty bottom void)
- Crisp bold white headline
- 16:9 or 4:3 video centered vertically
- Subtle @vformemes watermark
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONT_PATH = str(ASSETS_DIR / "Montserrat-Bold.ttf")

# Auto-detect FFmpeg
FFMPEG = os.getenv("FFMPEG_PATH") or shutil.which("ffmpeg") or "ffmpeg"

W, H = 1080, 1920

def create_dark_overlay(lines, watermark="@vformemes", font_size=42, line_spacing=62, text_start_y=520, wm_y=1328):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if os.path.exists(FONT_PATH):
        font = ImageFont.truetype(FONT_PATH, font_size)
        wm_font = ImageFont.truetype(FONT_PATH, 26)
    else:
        font = ImageFont.load_default()
        wm_font = ImageFont.load_default()

    # 1. Draw Text Header Lines (Centered, Crisp White)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (W - lw) // 2
        y = text_start_y + (i * line_spacing)
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    # 2. Draw Subtle Watermark
    if watermark:
        wm_bbox = draw.textbbox((0, 0), watermark, font=wm_font)
        wm_w = wm_bbox[2] - wm_bbox[0]
        wm_x = (W - wm_w) // 2
        draw.text((wm_x, wm_y), watermark, font=wm_font, fill=(160, 160, 160, 220))

    return overlay

def render_centered_meme(
    video_in: str,
    lines: list,
    output_mp4: str,
    duration: float = 7.5,
    aspect: str = "16:9",
    watermark: str = "@vformemes",
    ss_offset: float = 0
):
    vid_w = 1080
    if aspect == "16:9":
        vid_h = int(vid_w * 9 / 16) # 608px
        vid_y = 680
        text_y = 520
        wm_y = vid_y + vid_h + 40   # 1328px
    else: # 4:3
        vid_h = int(vid_w * 3 / 4) # 810px
        vid_y = 600
        text_y = 440
        wm_y = vid_y + vid_h + 40   # 1450px

    overlay_img = create_dark_overlay(
        lines,
        watermark=watermark,
        font_size=42,
        line_spacing=62,
        text_start_y=text_y,
        wm_y=wm_y
    )
    overlay_path = output_mp4 + ".overlay_tmp.png"
    overlay_img.save(overlay_path)

    fade_start = max(0, duration - 1.2)
    filter_complex = (
        f"color=c=black:s=1080x1920:d={duration}[bg];"
        f"[0:v]scale={vid_w}:{vid_h}:force_original_aspect_ratio=increase,crop={vid_w}:{vid_h},format=yuv420p[vid];"
        f"[bg][vid]overlay=0:{vid_y}[comp];"
        f"[comp][1:v]overlay=0:0[vfinal];"
        f"[0:a]atrim=0:{duration},afade=t=out:st={fade_start}:d=1.2[afinal]"
    )

    cmd = [FFMPEG, "-y"]
    if ss_offset > 0:
        cmd.extend(["-ss", str(ss_offset)])
    cmd.extend([
        "-i", video_in,
        "-i", overlay_path,
        "-t", str(duration),
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4
    ])

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        if os.path.exists(overlay_path):
            try:
                os.remove(overlay_path)
            except Exception:
                pass
