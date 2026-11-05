#!/usr/bin/env python3
"""
Batch Meme Reel Renderer & Google Drive Uploader
Generates reels with Centered Dark Theme (Option A):
- Pure black canvas (1080x1920)
- Eye-level optical center ratio
- Crisp bold white headline
- 16:9 or 4:3 video centered vertically
- Subtle @vformemes watermark
- Auto-mixes background music if input video has no audio
- Auto-uploads directly to Google Drive memes queue folder
"""

import os
import sys
import json
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/home/vivek/.cache/uv/archive-v0/EZYQvKIT2LrBUmr7/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2"
if not os.path.exists(FFMPEG):
    FFMPEG = "/home/vivek/nifi/meme_build/ffmpeg"
if not os.path.exists(FFMPEG):
    FFMPEG = "ffmpeg"

WORK_DIR = "/home/vivek/nifi/meme_build"
OUT_DIR = "/home/vivek/nifi"
FONT_PATH = os.path.join(WORK_DIR, "Montserrat-Bold.ttf")
DEFAULT_AUDIO = os.path.join(WORK_DIR, "audio.mp3")
DRIVE_FOLDER_ID = "15tEG1buRhHi8g4lkv98KMJC_-LHupuvV"

W, H = 1080, 1920

def create_dark_overlay(lines, watermark="@vformemes", font_size=42, line_spacing=62, text_start_y=520, wm_y=1328):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = ImageFont.truetype(FONT_PATH, font_size)
    wm_font = ImageFont.truetype(FONT_PATH, 26)

    # 1. Headline Text (Centered, Crisp White)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (W - lw) // 2
        y = text_start_y + (i * line_spacing)
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    # 2. Subtle Watermark
    if watermark:
        wm_bbox = draw.textbbox((0, 0), watermark, font=wm_font)
        wm_w = wm_bbox[2] - wm_bbox[0]
        wm_x = (W - wm_w) // 2
        draw.text((wm_x, wm_y), watermark, font=wm_font, fill=(160, 160, 160, 220))

    return overlay

def check_has_audio(video_in):
    res = subprocess.run([FFMPEG, '-i', video_in], stderr=subprocess.PIPE, text=True)
    return 'Audio:' in res.stderr

def render_meme(video_in, lines, output_mp4, duration=7.0, aspect="16:9", watermark="@vformemes", ss_offset=0):
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
    overlay_path = os.path.join(WORK_DIR, f"overlay_{os.path.basename(output_mp4)}.png")
    overlay_img.save(overlay_path)

    has_audio = check_has_audio(video_in)
    fade_start = max(0, duration - 1.2)

    cmd = [FFMPEG, "-y"]
    if ss_offset > 0:
        cmd.extend(["-ss", str(ss_offset)])
    cmd.extend(["-i", video_in, "-i", overlay_path])

    if has_audio:
        filter_complex = (
            f"color=c=black:s=1080x1920:d={duration}[bg];"
            f"[0:v]scale={vid_w}:{vid_h}:force_original_aspect_ratio=increase,crop={vid_w}:{vid_h},format=yuv420p[vid];"
            f"[bg][vid]overlay=0:{vid_y}[comp];"
            f"[comp][1:v]overlay=0:0[vfinal];"
            f"[0:a]atrim=0:{duration},afade=t=out:st={fade_start}:d=1.2[afinal]"
        )
    else:
        cmd.extend(["-i", DEFAULT_AUDIO])
        filter_complex = (
            f"color=c=black:s=1080x1920:d={duration}[bg];"
            f"[0:v]scale={vid_w}:{vid_h}:force_original_aspect_ratio=increase,crop={vid_w}:{vid_h},format=yuv420p[vid];"
            f"[bg][vid]overlay=0:{vid_y}[comp];"
            f"[comp][1:v]overlay=0:0[vfinal];"
            f"[2:a]atrim=0:{duration},afade=t=out:st={fade_start}:d=1.2[afinal]"
        )

    cmd.extend([
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

    print(f"Rendering: {output_mp4} ...")
    subprocess.run(cmd, check=True)
    size = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"Finished rendering: {output_mp4} ({size:.2f} MB)")

    # Cleanup temp overlay
    try:
        os.remove(overlay_path)
    except Exception:
        pass

def get_next_reel_number():
    res = subprocess.run(['gdrive', 'readonly', 'ls', DRIVE_FOLDER_ID, '--max', '0', '--json'], stdout=subprocess.PIPE, text=True)
    highest = 33
    if res.returncode == 0:
        try:
            items = json.loads(res.stdout)
            for item in items:
                name = item.get('name', '')
                m = re.match(r'reel_(\d+)_', name)
                if m:
                    highest = max(highest, int(m.group(1)))
        except Exception:
            pass
    return highest + 1

def main():
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            meme_specs = json.load(f)
    else:
        print("Error: Please provide path to meme specs JSON file.", file=sys.stderr)
        sys.exit(1)

    start_num = get_next_reel_number()
    print(f"Starting batch render from reel index: {start_num}")

    uploaded_files = []

    for i, spec in enumerate(meme_specs):
        reel_num = start_num + i
        slug = spec.get('slug', f'meme_{reel_num}')
        raw_vid = os.path.join(WORK_DIR, spec.get('raw_video', 'cillian_raw.mp4'))
        lines = spec.get('lines', [])
        duration = spec.get('duration', 7.0)
        aspect = spec.get('aspect', '16:9')
        ss_offset = spec.get('ss_offset', 0)
        watermark = spec.get('watermark', '@vformemes')

        out_name = f"reel_{reel_num}_{slug}.mp4"
        out_path = os.path.join(OUT_DIR, out_name)

        print(f"\n--- Processing [{i+1}/{len(meme_specs)}]: #{reel_num} {out_name} ---")
        render_meme(
            video_in=raw_vid,
            lines=lines,
            output_mp4=out_path,
            duration=duration,
            aspect=aspect,
            watermark=watermark,
            ss_offset=ss_offset
        )

        # Upload directly to Google Drive
        print(f"Uploading {out_name} to Google Drive...")
        up_res = subprocess.run(
            ['gdrive', 'mutate', 'upload', out_path, '--parent', DRIVE_FOLDER_ID, '--json'],
            stdout=subprocess.PIPE, text=True
        )
        if up_res.returncode == 0:
            print(f"Successfully uploaded {out_name} to Google Drive!")
            uploaded_files.append(out_path)
        else:
            print(f"Failed to upload {out_name} to Google Drive: {up_res.stderr}", file=sys.stderr)

    print(f"\nBatch rendering & Drive upload complete! Total uploaded: {len(uploaded_files)}")

if __name__ == '__main__':
    main()
