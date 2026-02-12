import os
import argparse
from utils.directory import create_directory_structure
from utils.download import is_youtube_url, download_youtube_video
from models.model_loader import initialize_models
from processors.video_processor import process_video
from utils.cleanup import clean_temp_directory

def main():
    parser = argparse.ArgumentParser(description="Video Translation CLI")
    parser.add_argument("--url", type=str, required=True, help="YouTube URL or local file path")
    parser.add_argument("--model", type=str, choices=["mira", "qwen"], required=True, help="Choose model: 'mira' (Port 7000) or 'qwen' (Port 9000)")
    
    args = parser.parse_args()

    # define a API baseada na escolha
    if args.model == "mira":
        API_URL = "http://44.192.41.163:7000/voice_clone"
        print(f"\n[Config] Using MIRA Model (Port 7000)")
    else:
        API_URL = "http://44.192.41.163:9000/voice_clone"
        print(f"\n[Config] Using QWEN Model (Port 9000)")

    try:
        print("\n=== Video Translation System ===")
        print("\nStep 1: Creating working directories...")
        directories = create_directory_structure()
        
        clean_temp_directory(directories['temp'])
        
        print("\nStep 2: Initializing models...")
        _, pipe = initialize_models(directories['models'])

        print(f"\nStep 3: Processing Input: {args.url}")
        video_input = args.url
        
        if is_youtube_url(video_input):
            print("YouTube URL detected")
            video_path = download_youtube_video(video_input, directories['temp'])
        else:
            video_path = video_input
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

        print(f"\nStep 4: Processing video using API...")
        
        output_video_path = process_video(
            video_path, 
            directories['temp'], 
            API_URL, 
            pipe, 
            directories['videos'],
            model_name=args.model 
        )

        print("\nStep 5: Cleanup")
        clean_temp_directory(directories['temp'])

        print(f"\n✓ Translation complete!")
        print(f"Output saved as: {output_video_path}")
        print("\nProcess finished successfully!")

    except Exception as e:
        print(f"\nError: {e}")
        print("Translation process failed.")
        try:
            clean_temp_directory(directories['temp'])
        except:
            pass
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())