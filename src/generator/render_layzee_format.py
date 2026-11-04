#!/usr/bin/env python3
import os
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/home/vivek/nifi/meme_build/ffmpeg"
WORK_DIR = "/home/vivek/nifi/meme_build"
FONT_PATH = os.path.join(WORK_DIR, "Montserrat-Bold.ttf")

W, H = 1080, 1920

def create_layzee_overlay(lines, watermark="@layzee_hub_", font_size=44, line_spacing=64, text_start_y=380, wm_y=1450):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = ImageFont.truetype(FONT_PATH, font_size)
    wm_font = ImageFont.truetype(FONT_PATH, 26)

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
        draw.text((wm_x, wm_y), watermark, font=wm_font, fill=(170, 170, 170, 220))

    return overlay

def render_layzee_reel(video_in, lines, output_mp4, duration=7.5, aspect="16:9", watermark="@layzee_hub_", ss_offset=0):
    vid_w = 1080
    if aspect == "16:9":
        vid_h = int(vid_w * 9 / 16) # 608
        vid_y = 660
        text_y = 420
        wm_y = vid_y + vid_h + 60
    else: # 4:3
        vid_h = int(vid_w * 3 / 4) # 810
        vid_y = 560
        text_y = 350
        wm_y = vid_y + vid_h + 50

    overlay_img = create_layzee_overlay(
        lines,
        watermark=watermark,
        font_size=44,
        line_spacing=64,
        text_start_y=text_y,
        wm_y=wm_y
    )
    overlay_path = os.path.join(WORK_DIR, "layzee_overlay_tmp.png")
    overlay_img.save(overlay_path)

    fade_start = max(0, duration - 1.2)
    filter_complex = (
        f"color=c=black:s=1080x1920:d={duration}[bg];"
        f"[0:v]scale={vid_w}:{vid_h}:force_original_aspect_ratio=increase,crop={vid_w}:{vid_h},format=yuv420p[vid];"
        f"[bg][vid]overlay=0:{vid_y}[comp];"
        f"[comp][1:v]overlay=0:0[vfinal];"
        f"[0:a]atrim=0:{duration},afade=t=out:st={fade_start}:d=1.2[afinal]"
    )

    cmd = [
        FFMPEG, "-y"
    ]
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

    print(f"Rendering @layzee_hub_ style sample: {output_mp4} ...")
    subprocess.run(cmd, check=True)
    print(f"Done rendering! Size: {os.path.getsize(output_mp4) / (1024*1024):.2f} MB")

    # Generate a preview frame jpg
    preview_frame = output_mp4.replace(".mp4", "_preview.jpg")
    subprocess.run([
        FFMPEG, "-y",
        "-ss", "00:00:02",
        "-i", output_mp4,
        "-vframes", "1",
        "-q:v", "2",
        preview_frame
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Preview frame generated: {preview_frame}")

    try:
        os.remove(overlay_path)
    except Exception:
        pass

if __name__ == '__main__':
    video_input = os.path.join(WORK_DIR, "nana_raw.mp4")
    sample_lines = [
        "Class ki sabse topper ladki ne",
        "bhi reject kar diya"
    ]
    out_file = "/home/vivek/nifi/sample_layzee_reel.mp4"
    render_layzee_reel(video_input, sample_lines, out_file, duration=7.5, aspect="4:3", watermark="@layzee_hub_")
