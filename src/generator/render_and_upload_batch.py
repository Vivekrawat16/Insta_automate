#!/usr/bin/env python3
import os
import sys
import json
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/home/vivek/.cache/uv/archive-v0/EZYQvKIT2LrBUmr7/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2"
if not os.path.exists(FFMPEG):
    FFMPEG = "/home/vivek/nifi/meme_build/ffmpeg"

WORK_DIR = "/home/vivek/nifi/meme_build"
OUT_DIR = "/home/vivek/nifi"
FONT_PATH = os.path.join(WORK_DIR, "Montserrat-Bold.ttf")
SKULL_PATH = os.path.join(WORK_DIR, "apple_skull.png")
DEFAULT_AUDIO = os.path.join(WORK_DIR, "audio.mp3")
DRIVE_FOLDER_ID = "15tEG1buRhHi8g4lkv98KMJC_-LHupuvV"

W, H = 1080, 1920

def create_overlay(lines, card_y1=150, card_h=350, font_size=36, line_spacing=56):
    card_w = 970
    card_x1 = (W - card_w) // 2
    card_radius = 28

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Pure Solid White Card
    draw.rounded_rectangle(
        [(card_x1, card_y1), (card_x1 + card_w, card_y1 + card_h)],
        radius=card_radius,
        fill=(255, 255, 255, 255)
    )

    font = ImageFont.truetype(FONT_PATH, font_size)
    total_text_h = len(lines) * line_spacing - 10
    text_start_y = card_y1 + (card_h - total_text_h) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]

        if i == len(lines) - 1:
            skull = Image.open(SKULL_PATH).convert("RGBA")
            emoji_size = int(font_size * 1.15)
            skull = skull.resize((emoji_size, emoji_size), Image.Resampling.LANCZOS)
            spacing = 14
            full_line_w = line_w + spacing + emoji_size
            line_x = card_x1 + (card_w - full_line_w) // 2
            line_y = text_start_y + i * line_spacing

            draw.text((line_x, line_y), line, font=font, fill=(12, 12, 12, 255))
            emoji_x = line_x + line_w + spacing
            emoji_y = line_y + (bbox[3] - bbox[1] - emoji_size) // 2 + 2
            overlay.paste(skull, (int(emoji_x), int(emoji_y)), skull)
        else:
            line_x = card_x1 + (card_w - line_w) // 2
            line_y = text_start_y + i * line_spacing
            draw.text((line_x, line_y), line, font=font, fill=(12, 12, 12, 255))

    return overlay, card_x1, card_y1, card_w, card_h

def check_has_audio(video_in):
    res = subprocess.run([FFMPEG, '-i', video_in], stderr=subprocess.PIPE, text=True)
    return 'Audio:' in res.stderr

def render_meme(video_in, lines, output_mp4, duration=7.0, aspect="16:9", card_h=350, font_size=36, line_spacing=56, ss_offset=0):
    overlay_img, card_x1, card_y1, card_w, card_h = create_overlay(
        lines, card_y1=150, card_h=card_h, font_size=font_size, line_spacing=line_spacing
    )
    overlay_path = os.path.join(WORK_DIR, f"overlay_{os.path.basename(output_mp4)}.png")
    overlay_img.save(overlay_path)

    vid_w = 970
    if aspect == "16:9":
        vid_h = int(vid_w * 9 / 16)
        vid_y = card_y1 + card_h + 35
    else:  # 4:3
        vid_h = int(vid_w * 3 / 4)
        vid_y = card_y1 + card_h + 25

    mask_img = Image.new("RGBA", (vid_w, vid_h), (0, 0, 0, 0))
    ImageDraw.Draw(mask_img).rounded_rectangle([(0, 0), (vid_w, vid_h)], radius=24, fill=(255, 255, 255, 255))
    mask_path = os.path.join(WORK_DIR, f"mask_{os.path.basename(output_mp4)}.png")
    mask_img.save(mask_path)

    has_audio = check_has_audio(video_in)
    fade_start = max(0, duration - 1.2)

    cmd = [FFMPEG, "-y"]
    if ss_offset > 0:
        cmd.extend(["-ss", str(ss_offset)])
    cmd.extend(["-i", video_in, "-i", mask_path, "-i", overlay_path])

    if has_audio:
        filter_complex = (
            f"color=c=black:s=1080x1920:d={duration}[bg];"
            f"[0:v]scale={vid_w}:{vid_h},format=yuva420p[fg_raw];"
            f"[1:v]format=yuva420p[mask_layer];"
            f"[fg_raw][mask_layer]alphamerge[fg_rounded];"
            f"[bg][fg_rounded]overlay={card_x1}:{vid_y}[comp1];"
            f"[comp1][2:v]overlay=0:0[vfinal];"
            f"[0:a]atrim=0:{duration},afade=t=out:st={fade_start}:d=1.2[afinal]"
        )
    else:
        cmd.extend(["-i", DEFAULT_AUDIO])
        filter_complex = (
            f"color=c=black:s=1080x1920:d={duration}[bg];"
            f"[0:v]scale={vid_w}:{vid_h},format=yuva420p[fg_raw];"
            f"[1:v]format=yuva420p[mask_layer];"
            f"[fg_raw][mask_layer]alphamerge[fg_rounded];"
            f"[bg][fg_rounded]overlay={card_x1}:{vid_y}[comp1];"
            f"[comp1][2:v]overlay=0:0[vfinal];"
            f"[3:a]atrim=0:{duration},afade=t=out:st={fade_start}:d=1.2[afinal]"
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

    # Cleanup temp overlays
    try:
        os.remove(overlay_path)
        os.remove(mask_path)
    except Exception:
        pass

def get_next_reel_number():
    res = subprocess.run(['gdrive', 'readonly', 'ls', DRIVE_FOLDER_ID, '--max', '0', '--json'], stdout=subprocess.PIPE, text=True)
    highest = 14
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
        card_h = spec.get('card_h', 350)
        font_size = spec.get('font_size', 35)
        line_spacing = spec.get('line_spacing', 54)
        ss_offset = spec.get('ss_offset', 0)

        out_name = f"reel_{reel_num}_{slug}.mp4"
        out_path = os.path.join(OUT_DIR, out_name)

        print(f"\n--- [{i+1}/{len(meme_specs)}] Processing: {out_name} ---")
        render_meme(raw_vid, lines, out_path, duration=duration, aspect=aspect, card_h=card_h, font_size=font_size, line_spacing=line_spacing, ss_offset=ss_offset)

        # Upload to Google Drive
        print(f"Uploading {out_name} to Google Drive folder {DRIVE_FOLDER_ID}...")
        up_res = subprocess.run(['gdrive', 'mutate', 'upload', out_path, '--parent', DRIVE_FOLDER_ID], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if up_res.returncode == 0:
            print(f"Successfully uploaded: {out_name}")
            uploaded_files.append(out_name)
            try:
                os.remove(out_path)
            except Exception:
                pass
        else:
            print(f"Failed to upload {out_name}: {up_res.stderr.strip()}", file=sys.stderr)

    print(f"\nBatch processing complete! Total uploaded to Google Drive: {len(uploaded_files)}/{len(meme_specs)}")

if __name__ == '__main__':
    main()
