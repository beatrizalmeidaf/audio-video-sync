import os
import argparse
from utils.directory import create_directory_structure
from utils.download import is_youtube_url, download_youtube_video
from processors.video_processor import process_video
from utils.cleanup import clean_temp_directory

def main():
    parser = argparse.ArgumentParser(description="Video Translation CLI")
    parser.add_argument("--url", type=str, required=True, help="YouTube URL or local file path")
    parser.add_argument("--model", type=str, choices=["mira", "qwen"], required=True, help="Choose model: 'mira' or 'qwen'")
    args = parser.parse_args()

    API_URL = "http://44.192.41.163:7000/voice_clone" if args.model == "mira" else "http://13.220.246.239:9000/voice_clone"
    print(f"\n[Config] Using {args.model.upper()} Model")

    try:
        print("\n=== Video Translation System ===")
        directories = create_directory_structure()
        clean_temp_directory(directories['temp'])
        
        video_input = args.url
        if is_youtube_url(video_input):
            video_path = download_youtube_video(video_input, directories['temp'])
        else:
            video_path = video_input
            if not os.path.exists(video_path): raise FileNotFoundError(f"File not found: {video_path}")

    
        output_video_path = process_video(
            video_path, 
            directories['temp'], 
            API_URL, 
            directories['videos'],
            model_name=args.model
        )

        clean_temp_directory(directories['temp'])
        print(f"\n✓ Translation complete! Output saved as: {output_video_path}")

    except Exception as e:
        print(f"\nError: {e}")
        try: clean_temp_directory(directories['temp'])
        except: pass
        return 1
    return 0

if __name__ == "__main__":
    exit(main())