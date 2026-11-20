# python-scripts

Small Python tools I wrote because I got tired of doing the same things by hand. One file each, run them from the command line, no framework, no drama.

| Script | What it does |
|---|---|
| `youtube_outliers.py` | Finds YouTube videos that got way more views than their channel normally gets. If a channel averages 2k views and one video hit 400k, something in that video worked, and this script tells you which one. |
| `free_image_search.py` | Finds images you're actually allowed to use (CC0, public domain, CC BY, CC BY-SA) on Wikimedia Commons and Openverse. Saves who made them and under what license, so "where did you get this?" has an answer. |
| `pixabay_videos.py` | Grabs stock clips from Pixabay and trims them into 12 second, edit-ready pieces. Has a vertical mode for shorts, because apparently everything is vertical now. |
| `strip_metadata.py` | Removes metadata (EXIF, GPS, encoder tags, chapters) from images, videos and audio. Your vacation photo doesn't need to tell the internet where you live. |

## Setup

Python 3.9+ and [ffmpeg](https://ffmpeg.org/) on your PATH. If you don't have ffmpeg yet, you'll want it anyway.

```
pip install -r requirements.txt
```

`pixabay_videos.py` needs a free Pixabay API key in the `PIXABAY_API_KEY` environment variable. Takes two minutes to get one.

## Examples

```
python youtube_outliers.py queries.txt results.json --per-query 30
python free_image_search.py images/ bridge "golden gate bridge fog" --n 6
python pixabay_videos.py clips/ ocean "ocean waves sunset" --n 4
python strip_metadata.py final.mp4 thumbnail.png
```

Forgot the arguments? `-h` works on all of them. I forget them too.

## Notes

- Images and clips keep their original licenses. The script saves the credits, reading them is on you.
- `youtube_outliers.py` only reads public data through yt-dlp. Be nice and don't hammer it with 500 queries at once.

## License

MIT. Use it, change it, break it, fix it.
