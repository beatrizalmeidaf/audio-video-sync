from yt_dlp import YoutubeDL
from .cleanup import clean_temp_directory
import os
import subprocess

def is_youtube_url(url):
    return "youtube.com" in url or "youtu.be" in url


def download_youtube_video(url, temp_dir):
    try:
        print("\nDownloading YouTube video...")
        clean_temp_directory(temp_dir)

        output_path = os.path.join(temp_dir, "youtube_video.%(ext)s")
        final_path = os.path.join(temp_dir, "youtube_video.mp4")

        ydl_opts = {
            "format": "bv*+ba/best",
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": False,
            "sleep_interval": 5,
            "max_sleep_interval": 10,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            },
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Mobile Safari/537.36"
                )
            }
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(final_path):
            raise Exception("Download failed - output file not found")

        trimmed_path = os.path.join(temp_dir, "youtube_video_30s.mp4")

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", final_path,
            "-ss", "0",
            "-t", "30",
            "-c", "copy",
            trimmed_path
        ], check=True)

        return trimmed_path

    except Exception as e:
        raise Exception(f"Error downloading YouTube video: {e}")
