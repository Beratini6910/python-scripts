# python-scripts

Small Python tools I use for content research and media work. Each one is a single file you can run from the command line.

| Script | What it does |
|---|---|
| `youtube_outliers.py` | Searches YouTube for a list of queries and finds videos that got many times more views than their channel's median. Good for spotting topics that are working right now. |
| `free_image_search.py` | Finds commercially usable images (CC0, public domain, CC BY, CC BY-SA) on Wikimedia Commons and Openverse, downloads them and saves author/license info for attribution. |
| `pixabay_videos.py` | Searches Pixabay stock videos, downloads and trims them into edit-ready 12s clips. Supports vertical clips for shorts. |
| `strip_metadata.py` | Removes metadata (EXIF, GPS, encoder tags, chapters) from images, videos and audio before you publish them. |

## Setup

Python 3.9+ and [ffmpeg](https://ffmpeg.org/) on your PATH.

```
pip install -r requirements.txt
```

`pixabay_videos.py` needs a free Pixabay API key in the `PIXABAY_API_KEY` environment variable.

## Examples

```
python youtube_outliers.py queries.txt results.json --per-query 30
python free_image_search.py images/ bridge "golden gate bridge fog" --n 6
python pixabay_videos.py clips/ ocean "ocean waves sunset" --n 4
python strip_metadata.py final.mp4 thumbnail.png
```

Each script also prints its usage with `-h`.

## Notes

- Images and clips keep their original licenses. Check the saved credits file before publishing.
- `youtube_outliers.py` only reads public video data through yt-dlp. Keep the request volume reasonable.

## License

MIT
