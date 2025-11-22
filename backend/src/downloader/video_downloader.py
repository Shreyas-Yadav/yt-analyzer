import os
import yt_dlp

class VideoDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def download_video(self, url):
        """
        Downloads a video from the given URL.
        Returns the path to the downloaded file.
        """
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return {
                    "filename": filename,
                    "title": info.get('title', 'Unknown Title'),
                    "url": url
                }
        except Exception as e:
            print(f"Error downloading video: {e}")
            raise e

    def list_videos(self):
        """
        Returns a list of downloaded video files.
        """
        if not os.path.exists(self.output_dir):
            return []
        
        files = []
        for filename in os.listdir(self.output_dir):
            # Filter for video files if needed, for now just list all files
            if os.path.isfile(os.path.join(self.output_dir, filename)):
                files.append(filename)
        return files
