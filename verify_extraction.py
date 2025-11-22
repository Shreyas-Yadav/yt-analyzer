import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'backend', 'src'))

from downloader.video_downloader import VideoDownloader

def verify():
    print("Starting verification...")
    downloader = VideoDownloader(output_dir="backend/downloads")
    
    # Test URL (short video)
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    print(f"Downloading video from {url}...")
    try:
        result = downloader.download_video(url)
        video_path = result['filename']
        print(f"Video downloaded to: {video_path}")
        
        if not os.path.exists(video_path):
            print("ERROR: Video file not found!")
            return
            
        if "videos" not in video_path:
             print("ERROR: Video not in 'videos' subdirectory!")
             
    except Exception as e:
        print(f"Download failed: {e}")
        return

    print("Extracting audio...")
    try:
        audio_path = downloader.extract_audio(video_path)
        print(f"Audio extracted to: {audio_path}")
        
        if not os.path.exists(audio_path):
            print("ERROR: Audio file not found!")
            return
            
        if "audio" not in audio_path:
            print("ERROR: Audio not in 'audio' subdirectory!")
            
        print("Verification SUCCESS!")
        
        # Cleanup
        # os.remove(video_path)
        # os.remove(audio_path)
        
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    verify()
