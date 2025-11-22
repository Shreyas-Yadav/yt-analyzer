import os
import yt_dlp
import ffmpeg

class VideoDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = output_dir
        self.videos_dir = os.path.join(output_dir, "videos")
        self.audio_dir = os.path.join(output_dir, "audio")
        
        if not os.path.exists(self.videos_dir):
            os.makedirs(self.videos_dir)
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    def download_video(self, url):
        """
        Downloads a video from the given URL.
        Returns the path to the downloaded file.
        """
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.videos_dir, '%(title)s.%(ext)s'),
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

    def extract_audio(self, video_path):
        """
        Extracts audio from the video file.
        Returns the path to the extracted audio file.
        """
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # Construct audio filename
            video_filename = os.path.basename(video_path)
            audio_filename = os.path.splitext(video_filename)[0] + ".mp3"
            audio_path = os.path.join(self.audio_dir, audio_filename)

            # Extract audio using ffmpeg
            (
                ffmpeg
                .input(video_path)
                .output(audio_path)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            return audio_path
        except ffmpeg.Error as e:
            print(f"ffmpeg error: {e.stderr.decode('utf8')}")
            raise Exception(f"ffmpeg error: {e.stderr.decode('utf8')}")
        except Exception as e:
            print(f"Error extracting audio: {e}")
            raise e

    def list_videos(self):
        """
        Returns a list of downloaded video files.
        """
        if not os.path.exists(self.videos_dir):
            return []
        
        files = []
        for filename in os.listdir(self.videos_dir):
            # Filter for video files if needed, for now just list all files
            if os.path.isfile(os.path.join(self.videos_dir, filename)):
                files.append(filename)
        return files

    def delete_video(self, filepath):
        """
        Deletes the video file and associated audio file from the filesystem.
        """
        deleted = False
        
        # Delete video file
        if os.path.exists(filepath):
            os.remove(filepath)
            deleted = True
        
        # Delete associated audio file if it exists
        video_filename = os.path.basename(filepath)
        audio_filename = os.path.splitext(video_filename)[0] + ".mp3"
        audio_path = os.path.join(self.audio_dir, audio_filename)
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
            deleted = True
        
        return deleted
