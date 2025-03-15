from yt_dlp import YoutubeDL
from .cleanup import clean_temp_directory
import os

def is_youtube_url(url):
    return "youtube.com" in url or "youtu.be" in url

def download_youtube_video(url, temp_dir):
    try:
        print("\nDownloading first 30 seconds of YouTube video...")
        
        clean_temp_directory(temp_dir)
        
        output_path = os.path.join(temp_dir, 'youtube_video.mp4')
        
        if os.path.exists(output_path):
            os.remove(output_path)
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'postprocessor_args': [
                '-ss', '00:00:00',  
                '-t', '00:00:30'    
            ],
            'progress_hooks': [lambda d: print(f"Downloading: {d.get('_percent_str', '...')}")],
            'quiet': False,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if not os.path.exists(output_path):
            raise Exception("Download failed - output file not found")
            
        return output_path
    except Exception as e:
        raise Exception(f"Error downloading YouTube video: {e}")