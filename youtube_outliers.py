"""
Find YouTube videos that perform far above their channel's usual numbers.

For each search query it grabs the top results, then looks at the last 30
uploads (shorts + long videos) of every channel it found and compares each
video's views to that channel's median. A video with 20x the median is
usually worth a closer look.

Needs yt-dlp on PATH. No API key required.

    python youtube_outliers.py queries.txt results.json --per-query 30 --channels 25

queries.txt = one search query per line.
"""
import argparse
import json
import statistics
import subprocess
from concurrent.futures import ThreadPoolExecutor

FIELDS = "%(id)s\t%(view_count)s\t%(duration)s\t%(channel)s\t%(channel_url)s\t%(title)s"


def run_ytdlp(args, timeout=180):
    cmd = ["yt-dlp", "--skip-download", "--flat-playlist", "--print", FIELDS, *args]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return []

    videos = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 6 or not parts[1].isdigit():
            continue  # private/removed videos come back with NA views
        vid, views, duration, channel, channel_url, title = parts
        videos.append({
            "id": vid,
            "views": int(views),
            "duration": float(duration) if duration not in ("NA", "None", "") else None,
            "channel": channel,
            "channel_url": channel_url,
            "title": title,
        })
    return videos


def search(query, n):
    return [dict(v, query=query) for v in run_ytdlp([f"ytsearch{n}:{query}"])]


def channel_median(url):
    # shorts and regular uploads live on separate tabs
    views = []
    for tab in ("shorts", "videos"):
        views += [v["views"] for v in run_ytdlp([f"{url}/{tab}", "--playlist-end", "30"], timeout=120)]
    return url, int(statistics.median(views)) if views else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("queries")
    p.add_argument("output")
    p.add_argument("--per-query", type=int, default=30)
    p.add_argument("--channels", type=int, default=25, help="how many channels to measure")
    args = p.parse_args()

    with open(args.queries, encoding="utf-8") as f:
        queries = [q.strip() for q in f if q.strip()]

    with ThreadPoolExecutor(6) as pool:
        results = [v for batch in pool.map(lambda q: search(q, args.per_query), queries) for v in batch]

    # same video can show up for several queries
    unique = {}
    for v in results:
        unique.setdefault(v["id"], v)
    videos = sorted(unique.values(), key=lambda v: v["views"], reverse=True)

    channels = []
    for v in videos:
        if v["channel_url"] not in ("NA", "") and v["channel_url"] not in channels:
            channels.append(v["channel_url"])

    with ThreadPoolExecutor(6) as pool:
        medians = dict(pool.map(channel_median, channels[:args.channels]))

    for v in videos:
        m = medians.get(v["channel_url"])
        v["channel_median"] = m
        v["ratio"] = round(v["views"] / m, 1) if m else None

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=1)

    print(f"{len(videos)} videos, {len(medians)} channels measured")
    top = sorted((v for v in videos if v["ratio"]), key=lambda v: v["ratio"], reverse=True)[:40]
    for v in top:
        kind = "short" if v["duration"] and v["duration"] <= 180 else "long "
        print(f"{v['ratio']:>6}x {v['views']:>11,} {kind} | {v['channel'][:22]:22} | {v['title'][:70]}")


if __name__ == "__main__":
    main()
