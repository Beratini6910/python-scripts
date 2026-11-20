"""
Remove metadata from videos, audio and images before sharing them.

Video/audio (.mp4 .mov .mkv .wav .mp3 .m4a): global and stream tags, chapters,
encoder string and comments are dropped. Streams are copied, not re-encoded,
so it's fast and lossless.

Images (.jpg .jpeg .png .webp): only the pixels are rewritten, so EXIF
(camera, GPS), XMP and text chunks are gone.

Output goes next to the original as <name>-clean.<ext>. After each file it
prints whatever tags are still there so you can check.

    python strip_metadata.py video.mp4 photo.jpg ...
"""
import os
import subprocess
import sys

from PIL import Image

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")


def clean_media(src, dst):
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", src,
        "-map", "0", "-map_metadata", "-1", "-map_chapters", "-1",
        "-metadata", "comment=", "-metadata", "encoder=",
        "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact",
        "-c", "copy", dst,
    ], check=True)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "compact", dst],
        capture_output=True, text=True,
    )
    left = " ".join(probe.stdout.split())
    print(f"{os.path.basename(dst)}: remaining tags: {left or 'none'}")


def clean_image(src, dst):
    img = Image.open(src)
    # rebuild from raw pixels, nothing from img.info comes along
    clean = Image.frombytes(img.mode, img.size, img.tobytes())
    if dst.lower().endswith((".jpg", ".jpeg")):
        clean.save(dst, quality=95)
    else:
        clean.save(dst)
    print(f"{os.path.basename(dst)}: remaining info: {Image.open(dst).info or 'none'}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        name, ext = os.path.splitext(path)
        out = f"{name}-clean{ext}"
        if ext.lower() in IMAGE_EXT:
            clean_image(path, out)
        else:
            clean_media(path, out)


if __name__ == "__main__":
    main()
