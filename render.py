import json
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
FRAMES = OUT / "frames"
AUDIO = OUT / "audio"
OUT.mkdir(exist_ok=True)
FRAMES.mkdir(exist_ok=True)
AUDIO.mkdir(exist_ok=True)

def run(cmd):
    subprocess.run(cmd, check=True)

def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True
    )
    return float(result.stdout.strip())

def font(size):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()

def wrap_text(draw, text, face, max_width):
    lines, current = [], ""
    for char in text:
        candidate = current + char
        if draw.textbbox((0, 0), candidate, font=face)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines

def make_frame(scene, title, index):
    w, h = 1080, 1920
    image_path = scene.get("image")
    if image_path and (ROOT / image_path).exists():
        source = Image.open(ROOT / image_path).convert("RGB")
        canvas = ImageOps.fit(source, (w, h), method=Image.Resampling.LANCZOS)
    else:
        # Neutral fallback background; replace with your own licensed/created scene image.
        canvas = Image.new("RGB", (w, h), (30, 35, 48))
        px = canvas.load()
        for y in range(h):
            ratio = y / h
            color = (int(32 + 20 * ratio), int(43 + 16 * ratio), int(62 + 28 * ratio))
            for x in range(w):
                px[x, y] = color

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, w, 250), fill=(0, 0, 0, 75))
    od.rectangle((0, 1220, w, h), fill=(0, 0, 0, 165))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)

    title_font = font(42)
    caption_font = font(76)
    draw.text((72, 90), title[:34], font=title_font, fill=(255, 255, 255, 235),
              stroke_width=1, stroke_fill=(0, 0, 0, 160))

    caption = scene.get("caption", "")
    lines = wrap_text(draw, caption, caption_font, 900)
    line_height = 105
    total_height = len(lines) * line_height
    y = 1430 - total_height // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=caption_font, stroke_width=3)
        x = (w - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=caption_font, fill="white",
                  stroke_width=3, stroke_fill=(0, 0, 0, 220))
        y += line_height

    frame_path = FRAMES / f"scene_{index:02d}.png"
    canvas.convert("RGB").save(frame_path, quality=95)
    return frame_path

def main():
    cards_path = ROOT / "cards.json"
    if not cards_path.exists():
        raise FileNotFoundError("cards.json 파일이 없습니다. cards.example.json을 복사해 cards.json으로 저장하세요.")

    data = json.loads(cards_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    if not 2 <= len(scenes) <= 8:
        raise ValueError("scenes는 2개 이상 8개 이하여야 합니다.")
    for i, scene in enumerate(scenes, 1):
        if not scene.get("narration") or not scene.get("caption"):
            raise ValueError(f"{i}번 장면에 narration 또는 caption이 없습니다.")

    from melo.api import TTS
    tts = TTS(language="KR", device="cpu")
    speaker_ids = tts.hps.data.spk2id
    speaker = speaker_ids["KR"]
    speed = float(data.get("voice_speed", 1.0))
    title = data.get("title", "오늘의 피부 정보")

    segment_files = []
    concat_file = OUT / "concat.txt"

    for i, scene in enumerate(scenes, 1):
        print(f"[{i}/{len(scenes)}] 음성 및 장면 생성 중...")
        audio_path = AUDIO / f"voice_{i:02d}.wav"
        tts.tts_to_file(scene["narration"], speaker, str(audio_path), speed=speed)
        duration = get_duration(audio_path)
        frame_path = make_frame(scene, title, i)
        segment_path = OUT / f"segment_{i:02d}.mp4"

        run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "30",
            "-i", str(frame_path), "-i", str(audio_path),
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.3f}", "-shortest",
            "-movflags", "+faststart", str(segment_path)
        ])
        segment_files.append(segment_path)

    concat_file.write_text(
        "".join(f"file '{p.as_posix()}'\n" for p in segment_files),
        encoding="utf-8"
    )
    slug = "".join(c.lower() if c.isalnum() else "-" for c in title).strip("-")
    slug = "-".join(part for part in slug.split("-") if part)[:48] or "korean-short"
    final_path = OUT / f"{slug}.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy", "-movflags", "+faststart", str(final_path)
    ])
    print(f"완료: {final_path}")
    print(f"크기: {final_path.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()
