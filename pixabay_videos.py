"""
Search Pixabay for stock video clips and download trimmed, ready-to-edit copies.

Clips are cut to 12 seconds, audio removed, scaled to 1280px (or 1080px wide
for vertical clips) and re-encoded to H.264 30fps. Source page, author and
tags are saved to a JSON file, plus a preview image with the middle frame
of each clip.

Set your key first:  set PIXABAY_API_KEY=...   (Windows)
                     export PIXABAY_API_KEY=... (Linux/macOS)

    python pixabay_videos.py out/ ocean "ocean waves sunset" --n 4
    python pixabay_videos.py out/ city "city night traffic" --vertical
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

HEADERS = {"User-Agent": "pixabay-videos/1.0 (python script)"}
MAX_SECONDS = 12


def search(key, query, n, vertical):
    params = urllib.parse.urlencode({
        "key": key, "q": query, "safesearch": "true", "order": "popular",
        # vertical clips are rare, so ask for more and filter
        "per_page": 100 if vertical else max(n * 3, 10),
    })
    req = urllib.request.Request(f"https://pixabay.com/api/videos/?{params}", headers=HEADERS)
    data = json.load(urllib.request.urlopen(req, timeout=30))

    for hit in data.get("hits", []):
        v = hit["videos"].get("large") or hit["videos"].get("medium")
        if hit["duration"] < 4 or not v.get("url"):
            continue
        w, h = v.get("width", 0), v.get("height", 0)
        if vertical and not (h > w and w >= 720):
            continue
        if not vertical and w < 1280:
            continue
        yield {
            "url": v["url"],
            "page": hit["pageURL"],
            "author": hit["user"],
            "license": "Pixabay Content License",
            "duration": hit["duration"],
            "tags": hit["tags"],
        }


def save_clip(url, path, scale):
    tmp = path + ".tmp.mp4"
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120).read()
        with open(tmp, "wb") as f:
            f.write(data)
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", tmp, "-t", str(MAX_SECONDS), "-an",
            "-vf", f"{scale},fps=30", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", path,
        ], check=True)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def preview(frames, out_path, vertical):
    inputs = sum([["-i", f] for f in frames], [])
    size = "180:320" if vertical else "320:180"
    font = "C\\:/Windows/Fonts/arial.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    graph = "".join(
        f"[{i}]scale={size},drawtext=fontfile='{font}':text='{i + 1}':x=8:y=8:fontsize=26:"
        f"fontcolor=yellow:box=1:boxcolor=black[t{i}];" for i in range(len(frames))
    )
    graph += "".join(f"[t{i}]" for i in range(len(frames)))
    graph += f"hstack={len(frames)}" if len(frames) > 1 else "null"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, out_path])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("label")
    p.add_argument("query")
    p.add_argument("--n", type=int, default=4)
    p.add_argument("--vertical", action="store_true", help="only 9:16 clips (for shorts/reels)")
    args = p.parse_args()

    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        sys.exit("PIXABAY_API_KEY is not set")

    os.makedirs(args.folder, exist_ok=True)
    scale = "scale=1080:-2" if args.vertical else "scale=1280:-2"
    tag = "vert" if args.vertical else "clip"

    try:
        candidates = list(search(key, args.query, args.n, args.vertical))
    except Exception as e:
        # don't print the error text, the request URL has the API key in it
        sys.exit(f"search failed: {type(e).__name__}")

    credits, frames = {}, []
    for c in candidates:
        if len(credits) >= args.n:
            break
        name = f"{args.label}-{tag}{len(credits) + 1:02d}.mp4"
        path = os.path.join(args.folder, name)
        try:
            save_clip(c["url"], path, scale)
        except Exception:
            continue
        credits[name] = dict(c, query=args.query, url=c["url"].split("?")[0])

        frame = os.path.join(args.folder, f".{name}.jpg")
        middle = min(c["duration"], MAX_SECONDS) / 2
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(middle), "-i", path, "-frames:v", "1", frame])
        frames.append(frame)

    with open(os.path.join(args.folder, f"credits-{args.label}-{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(credits, f, ensure_ascii=False, indent=1)

    if frames:
        preview(frames, os.path.join(args.folder, f"{args.label}-{tag}-preview.jpg"), args.vertical)
        for fr in frames:
            os.remove(fr)
    print(f"{args.label}: {len(credits)} clips ({', '.join(credits)})")


if __name__ == "__main__":
    main()
