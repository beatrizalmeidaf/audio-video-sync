import os
from utils.directory import create_directory_structure
from utils.download import is_youtube_url, download_youtube_video
from models.model_loader import initialize_models
from processors.video_processor import process_video
from utils.cleanup import clean_temp_directory

def main():
    try:
        print("\n=== Video Translation System ===")
        print("\nStep 1: Creating working directories...")
        directories = create_directory_structure()
        print("✓ Directories created successfully")

        clean_temp_directory(directories['temp'])
        
        print("\nStep 2: Initializing models...")
        print("This may take several minutes on first run as models need to be downloaded...")
        tts, pipe = initialize_models(directories['models'])

        print("\nStep 3: Video Input")
        video_input = input("Enter the path to your video file or YouTube URL: ").strip()
        if not video_input:
            raise ValueError("Input cannot be empty")
        
        if is_youtube_url(video_input):
            print("YouTube URL detected")
            video_path = download_youtube_video(video_input, directories['temp'])
        else:
            video_path = video_input
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

        print("\nStep 4: Processing video...")
        output_video_path = process_video(video_path, directories['temp'], tts, pipe, directories['videos'])

        print("\nStep 5: Cleanup")
        print("Cleaning up temporary files...")
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