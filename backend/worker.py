import os
import json
import time
import boto3
import traceback
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from src.downloader.video_downloader import VideoDownloader
from src.database import SessionLocal, Video, Transcript, User, init_db
from src.utils import upload_to_s3, read_file_content

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
SQS_QUEUE_URL = os.getenv('SQS_TRANSCRIPTION_QUEUE_URL')
USE_S3 = bool(os.getenv('S3_BUCKET_NAME'))

# Initialize AWS Clients
try:
    sqs = boto3.client(
        'sqs',
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN')
    )
except Exception as e:
    print(f"Error initializing AWS clients: {e}")
    sqs = None

def process_message(message):
    """Process a single SQS message"""
    try:
        body = json.loads(message['Body'])
        video_id = body.get('video_id')
        url = body.get('url')
        user_id = body.get('user_id')
        
        print(f"Processing video {video_id}: {url}")
        
        db = SessionLocal()
        try:
            # Update status to processing
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = 'processing'
                db.commit()
            
            # Initialize downloader
            downloader = VideoDownloader(user_id=user_id)
            
            # 1. Download
            print("Downloading...")
            result = downloader.download_video(url)
            video_path = result['filename']
            video_title = result['title']
            
            # Update title in DB
            if video:
                video.title = video_title
                db.commit()
            
            # 2. Extract Audio
            print("Extracting audio...")
            audio_path = downloader.extract_audio(video_path)
            
            # 3. Transcribe
            print("Transcribing...")
            transcript_path = downloader.generate_transcript(audio_path, video_title)
            
            # 4. Upload to S3
            stored_transcript_path = transcript_path
            if USE_S3:
                print("Uploading to S3...")
                transcript_filename = os.path.basename(transcript_path)
                transcript_s3_key = f"transcripts/{user_id}/{transcript_filename}"
                stored_transcript_path = upload_to_s3(transcript_path, transcript_s3_key)
                
                # Cleanup local files
                if os.path.exists(video_path): os.remove(video_path)
                if os.path.exists(audio_path): os.remove(audio_path)
                if os.path.exists(transcript_path): os.remove(transcript_path)
            else:
                # Cleanup video/audio only
                if os.path.exists(video_path): os.remove(video_path)
                if os.path.exists(audio_path): os.remove(audio_path)
            
            # 5. Save Transcript to DB
            # Detect language
            detected_language = 'en'
            try:
                from langdetect import detect
                if stored_transcript_path.startswith("s3://"):
                    full_text = read_file_content(stored_transcript_path)
                    sample_text = full_text[:1000]
                else:
                    with open(stored_transcript_path, 'r', encoding='utf-8') as f:
                        sample_text = f.read(1000)
                
                lines = [line.split(']')[-1].strip() if ']' in line else line.strip() 
                        for line in sample_text.split('\n') if line.strip()]
                text_for_detection = ' '.join(lines[:10])
                if text_for_detection:
                    detected_language = detect(text_for_detection)
            except Exception as e:
                print(f"Language detection failed: {e}")

            # Find user
            user = db.query(User).filter(User.email == user_id).first()
            
            # DEBUG: Verify video exists
            check_video = db.query(Video).filter(Video.id == video_id).first()
            if not check_video:
                print(f"CRITICAL ERROR: Video {video_id} NOT FOUND in DB before transcript insertion!")
            else:
                print(f"DEBUG: Video {video_id} exists. Status: {check_video.status}")

            # Create transcript record
            db_transcript = Transcript(
                video_id=video_id,
                user_id=user.id,
                language=detected_language,
                file_path=stored_transcript_path
            )
            db.add(db_transcript)
            
            # Update video status
            if video:
                video.status = 'completed'
            
            db.commit()
            print(f"Successfully processed video {video_id}")
            
        except Exception as e:
            print(f"Error processing video: {e}")
            traceback.print_exc()
            if video:
                video.status = 'failed'
                db.commit()
            # IMPORTANT: Delete message even on failure to prevent infinite loop
            # In production, you might want to move to a Dead Letter Queue (DLQ)
            print(f"Deleting message {video_id} to prevent loop.")
            sqs.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
        finally:
            db.close()
            
    except Exception as e:
        print(f"Message processing failed: {e}")
        # If we can't even parse the message, we should probably delete it too
        # But for now, let's just log it.
        raise e

def main():
    print("Starting Worker...")
    if not SQS_QUEUE_URL:
        print("Error: SQS_TRANSCRIPTION_QUEUE_URL not set")
        return

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )
            
            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        process_message(message)
                        
                        # Delete message after successful processing
                        sqs.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        print(f"Failed to process message: {e}")
            else:
                print("No messages, waiting...")
                
        except Exception as e:
            print(f"Error in worker loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Ensure DB is initialized
    init_db()
    main()
