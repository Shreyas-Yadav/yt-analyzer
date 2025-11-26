import os
import yt_dlp
import ffmpeg
import whisper

class VideoDownloader:
    def __init__(self, output_dir="downloads", user_id=None):
        self.output_dir = output_dir
        self.user_id = user_id
        
        # Create user-specific subdirectories if user_id is provided
        if user_id:
            self.videos_dir = os.path.join(output_dir, "videos", user_id)
            self.audio_dir = os.path.join(output_dir, "audio", user_id)
            self.transcripts_dir = os.path.join(output_dir, "transcripts", user_id)
        else:
            self.videos_dir = os.path.join(output_dir, "videos")
            self.audio_dir = os.path.join(output_dir, "audio")
            self.transcripts_dir = os.path.join(output_dir, "transcripts")
        
        # Create directories if they don't exist
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.transcripts_dir, exist_ok=True)

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

    def generate_transcript(self, audio_path, video_title=None):
        """
        Generates transcript from audio file using Whisper.
        Returns the path to the transcript file.
        """
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Load Whisper model (tiny)
            print("Loading Whisper model...")
            model = whisper.load_model("tiny")
            
            # Transcribe audio
            print(f"Transcribing audio: {audio_path}")
            result = model.transcribe(audio_path)
            
            # Construct transcript filename
            if video_title:
                transcript_filename = video_title + ".txt"
            else:
                audio_filename = os.path.basename(audio_path)
                transcript_filename = os.path.splitext(audio_filename)[0] + ".txt"
            
            transcript_path = os.path.join(self.transcripts_dir, transcript_filename)
            
            # Write transcript with only plain text (no timestamps)
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(f"Transcript: {video_title or 'Unknown'}\n")
                f.write("=" * 80 + "\n\n")
                f.write(result['text'].strip() + "\n")

            
            print(f"Transcript saved to: {transcript_path}")
            return transcript_path
            
        except Exception as e:
            print(f"Error generating transcript: {e}")
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

    def delete_video(self, filepath, video_title):
        """
        Delete video, audio, and transcript files.
        Since we no longer store video path, we rely on video_title to find and delete transcripts.
        Video and audio files are already deleted after processing.
        """
        deleted = False
        
        # Video and audio files are already deleted after processing
        # We only need to delete transcript files
        
        # Delete associated transcript file if it exists
        if video_title:
            transcript_filename = video_title + ".txt"
            transcript_path = os.path.join(self.transcripts_dir, transcript_filename)
            
            if os.path.exists(transcript_path):
                os.remove(transcript_path)
                deleted = True
                
            # Also delete any translated transcripts
            import glob
            transcript_pattern = os.path.join(self.transcripts_dir, f"{video_title}_*.txt")
            for translated_file in glob.glob(transcript_pattern):
                if os.path.exists(translated_file):
                    os.remove(translated_file)
                    deleted = True
        
        return deleted
