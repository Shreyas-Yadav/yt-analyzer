import sys
import os

# Add the src directory to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from downloader.video_downloader import VideoDownloader

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <youtube_url>")
        return

    url = sys.argv[1]
    downloader = VideoDownloader()
    print(f"Downloading {url}...")
    try:
        filepath = downloader.download_video(url)
        print(f"Successfully downloaded to: {filepath}")
    except Exception as e:
        print(f"Failed to download: {e}")

if __name__ == "__main__":
    main()
