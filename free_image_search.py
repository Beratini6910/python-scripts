"""
Search Wikimedia Commons and Openverse for images you can use commercially
and download them with the license info saved next to them.

Only CC0, public domain, CC BY and CC BY-SA are kept. Author, license and
source page go into a JSON file so attribution is easy later. A contact sheet
(all results side by side, numbered) is made so you can pick quickly.

Needs ffmpeg on PATH.

    python free_image_search.py out/ bridge "golden gate bridge fog" --n 6
"""
import argparse
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request

HEADERS = {"User-Agent": "free-image-search/1.0 (python script)"}
ALLOWED = re.compile(
    r"^(cc0|pdm|public domain|cc by( |-)?(\d\.\d)?|cc by-sa( |-)?(\d\.\d)?|cc-by(-sa)?(-\d\.\d)?|by|by-sa)$", re.I
)
MIN_WIDTH = 800


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return json.load(urllib.request.urlopen(req, timeout=30))


def from_commons(query, n):
    params = urllib.parse.urlencode({
        "action": "query", "format": "json",
        "generator": "search", "gsrnamespace": 6, "gsrlimit": n * 2,
        "gsrsearch": f"filetype:bitmap {query}",
        "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1600,
    })
    pages = get_json(f"https://commons.wikimedia.org/w/api.php?{params}").get("query", {}).get("pages", {})
    for page in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        info = page["imageinfo"][0]
        meta = info.get("extmetadata", {})
        license_name = meta.get("LicenseShortName", {}).get("value", "").strip()
        if info.get("width", 0) < MIN_WIDTH or not ALLOWED.match(license_name):
            continue
        author = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "unknown")).strip()
        yield {
            "url": info.get("thumburl") or info["url"],
            "page": info["descriptionurl"],
            "license": license_name,
            "author": author,
            "title": page["title"],
        }


def from_openverse(query, n):
    params = urllib.parse.urlencode({"q": query, "license": "cc0,pdm,by,by-sa", "page_size": n * 2})
    for r in get_json(f"https://api.openverse.org/v1/images/?{params}").get("results", []):
        if (r.get("width") or 0) < MIN_WIDTH:
            continue
        yield {
            "url": r["url"],
            "page": r.get("foreign_landing_url") or r["url"],
            "license": f"CC {r['license'].upper()} {r.get('license_version') or ''}".strip(),
            "author": r.get("creator") or "unknown",
            "title": r.get("title") or "",
        }


def download_as_jpg(url, path):
    tmp = path + ".tmp"
    data = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40).read()
    with open(tmp, "wb") as f:
        f.write(data)
    # convert whatever we got (png, webp, tif...) to jpg, max 1600px wide
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", path],
                   check=True)
    os.remove(tmp)


def contact_sheet(files, out_path):
    inputs = sum([["-i", f] for f in files], [])
    font = "C\\:/Windows/Fonts/arial.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    tiles = "".join(
        f"[{i}]scale=320:200:force_original_aspect_ratio=decrease,pad=320:200:(ow-iw)/2:(oh-ih)/2,"
        f"drawtext=fontfile='{font}':text='{i + 1}':x=8:y=8:fontsize=28:fontcolor=yellow:box=1:boxcolor=black[t{i}];"
        for i in range(len(files))
    )
    if len(files) > 1:
        graph = tiles + "".join(f"[t{i}]" for i in range(len(files))) + f"hstack={len(files)}"
    else:
        graph = tiles + "[t0]null"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-frames:v", "1", out_path])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("label", help="file name prefix, e.g. 'bridge' -> bridge-01.jpg")
    p.add_argument("query")
    p.add_argument("--n", type=int, default=6)
    args = p.parse_args()
    os.makedirs(args.folder, exist_ok=True)

    candidates = []
    for source in (from_commons, from_openverse):
        try:
            candidates += list(source(args.query, args.n))
        except Exception as e:
            print(f"{source.__name__} failed: {e}")  # keep going with the other source

    credits, saved = {}, []
    for c in candidates:
        if len(saved) >= args.n:
            break
        name = f"{args.label}-{len(saved) + 1:02d}.jpg"
        path = os.path.join(args.folder, name)
        try:
            download_as_jpg(c["url"], path)
        except Exception:
            continue
        credits[name] = dict(c, query=args.query)
        saved.append(path)

    with open(os.path.join(args.folder, f"credits-{args.label}.json"), "w", encoding="utf-8") as f:
        json.dump(credits, f, ensure_ascii=False, indent=1)

    if saved:
        contact_sheet(saved, os.path.join(args.folder, f"{args.label}-preview.jpg"))
    print(f"{args.label}: {len(saved)} images ({', '.join(os.path.basename(s) for s in saved)})")


if __name__ == "__main__":
    main()
