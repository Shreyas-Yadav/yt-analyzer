from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os
import json
import datetime
import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables via config module (supports .env and AWS SSM)
import src.config

# Add the src directory to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from downloader.video_downloader import VideoDownloader
from translator.translator import Translator
from generator.flashcard_generator import FlashcardGenerator
from generator.quiz_generator import QuizGenerator
from database import init_db, get_db, Video, User, Transcript, Flashcard, Quiz

app = FastAPI()

# Initialize database
init_db()

# AWS Clients
try:
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    
    # Initialize S3 client if credentials are provided or available in environment
    if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
        s3 = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        sqs = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
    else:
        # Fallback to default credential provider chain
        s3 = boto3.client('s3', region_name=AWS_REGION)
        sqs = boto3.client('sqs', region_name=AWS_REGION)
        
    USE_S3 = bool(S3_BUCKET_NAME)
    SQS_QUEUE_URL = os.getenv('SQS_TRANSCRIPTION_QUEUE_URL')
    print(f"AWS Integration: S3={USE_S3} (Bucket: {S3_BUCKET_NAME}), SQS={bool(SQS_QUEUE_URL)}")
except Exception as e:
    print(f"Warning: AWS clients not initialized - {e}")
    USE_S3 = False
    s3 = None
    sqs = None
    S3_BUCKET_NAME = None
    SQS_QUEUE_URL = None

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str
    user_id: str = "anonymous" # Default to anonymous if not provided

class TranslateRequest(BaseModel):
    video_id: int
    target_language: str
    user_id: str = "anonymous"

class GenerateFlashcardsRequest(BaseModel):
    video_id: int
    language: str = "en"
    user_id: str

class SaveFlashcardsRequest(BaseModel):
    video_id: int
    user_id: str
    language: str
    flashcards: List[dict]

class GenerateQuizRequest(BaseModel):
    video_id: int
    language: str = "en"
    user_id: str

class SaveQuizRequest(BaseModel):
    video_id: int
    user_id: str
    language: str
    quiz: List[dict]

class UserLoginRequest(BaseModel):
    email: str

# ====================
# Helper Functions
# ====================

from src.utils import upload_to_s3, delete_from_s3, read_file_content, send_to_sqs, USE_S3, S3_BUCKET_NAME, SQS_QUEUE_URL

@app.post("/flashcards/save")
async def save_flashcards(request: SaveFlashcardsRequest, db: Session = Depends(get_db)):
    try:
        # 1. Save to File System
        # Create directory structure: downloads/flashcards/{user_id}/{video_id}
        base_dir = "downloads"
        flashcards_dir = os.path.join(base_dir, "flashcards", str(request.user_id), str(request.video_id))
        os.makedirs(flashcards_dir, exist_ok=True)

        # File path: flashcards_{language}.json
        filename = f"flashcards_{request.language}.json"
        file_path = os.path.join(flashcards_dir, filename)

        # Save to JSON file
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(request.flashcards, f, indent=4, ensure_ascii=False)

        # Upload to S3 if enabled
        if USE_S3:
            s3_key = f"flashcards/{request.user_id}/{request.video_id}/{filename}"
            stored_path = upload_to_s3(file_path, s3_key)
            # Optional: Delete local file after upload
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            stored_path = file_path

        # 2. Save to Database
        # Find user
        user = db.query(User).filter(User.email == request.user_id).first()
        if not user:
            # Should we create user? Or fail? 
            # For consistency with other endpoints, let's fail if user not found, 
            # but the frontend sends the email from AuthService.
            raise HTTPException(status_code=404, detail="User not found")

        # Find video
        video = db.query(Video).filter(Video.id == request.video_id, Video.user_id == user.id).first()
        if not video:
             raise HTTPException(status_code=404, detail="Video not found")

        # Check if flashcards already exist for this video/language
        existing_flashcard = db.query(Flashcard).filter(
            Flashcard.video_id == video.id,
            Flashcard.language == request.language
        ).first()

        if existing_flashcard:
            # Update existing
            existing_flashcard.file_path = stored_path
            existing_flashcard.created_at = datetime.datetime.utcnow() # Update timestamp
            db.commit()
            db.refresh(existing_flashcard)
            print(f"Updated existing flashcards for video {video.id} lang {request.language}")
        else:
            # Create new
            new_flashcard = Flashcard(
                video_id=video.id,
                user_id=user.id,
                language=request.language,
                file_path=stored_path
            )
            db.add(new_flashcard)
            db.commit()
            db.refresh(new_flashcard)
            print(f"Created new flashcards for video {video.id} lang {request.language}")

        return {"message": "Flashcards saved successfully", "path": stored_path}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error saving flashcards: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/login")
async def user_login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Called by frontend after successful Cognito authentication.
    Creates user in database if they don't exist.
    """
    try:
        # Find or create user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            user = User(email=request.email)
            db.add(user)
            db.commit()
            db.refresh(user)
            return {"message": "User created", "user": {"id": user.id, "email": user.email}}
        
        return {"message": "User already exists", "user": {"id": user.id, "email": user.email}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def queue_video_analysis(request: VideoRequest, db: Session = Depends(get_db)):
    """
    Queue video for analysis.
    Creates a DB record with status 'queued' and sends message to SQS.
    """
    try:
        # Find or create user
        user = db.query(User).filter(User.email == request.user_id).first()
        if not user:
            user = User(email=request.user_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create video record with 'queued' status
        # We don't have the title yet, so use URL or placeholder
        db_video = Video(
            user_id=user.id,
            title=f"Processing: {request.url}", # Placeholder, worker will update
            url=request.url,
            status='queued'
        )
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        # Send to SQS
        message = {
            "video_id": db_video.id,
            "url": request.url,
            "user_id": request.user_id
        }
        send_to_sqs(message)
        
        return {
            "message": "Video queued for analysis",
            "video_id": db_video.id,
            "status": "queued"
        }
            
    except Exception as e:
        print(f"Error queuing video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos")
async def list_videos(user_id: str = "anonymous", db: Session = Depends(get_db)):
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            return {"videos": []}
        
        videos = db.query(Video).filter(Video.user_id == user.id).all()
        return {
            "videos": [
                {
                    "id": v.id,
                    "title": v.title,
                    "url": v.url,
                    "status": v.status,
                    "created_at": v.created_at
                }
                for v in videos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{video_id}/transcripts")
async def get_video_transcripts(video_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    """Get all available transcripts for a specific video."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            return {"transcripts": []}
        
        # Verify video belongs to user
        video = db.query(Video).filter(Video.id == video_id, Video.user_id == user.id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get all transcripts for this video
        transcripts = db.query(Transcript).filter(Transcript.video_id == video_id).all()
        
        return {
            "transcripts": [
                {
                    "id": t.id,
                    "language": t.language,
                    "file_path": t.file_path,
                    "created_at": t.created_at
                }
                for t in transcripts
            ]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{video_id}/flashcards")
async def get_video_flashcards(video_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    """Get all saved flashcards for a specific video."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            return {"flashcards": []}
        
        # Verify video belongs to user
        video = db.query(Video).filter(Video.id == video_id, Video.user_id == user.id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get all flashcards for this video
        flashcards = db.query(Flashcard).filter(Flashcard.video_id == video_id).all()
        
        return {
            "flashcards": [
                {
                    "id": fc.id,
                    "language": fc.language,
                    "file_path": fc.file_path,
                    "created_at": fc.created_at
                }
                for fc in flashcards
            ]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/videos/{video_id}")
async def delete_video(video_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        video = db.query(Video).filter(Video.id == video_id, Video.user_id == user.id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Delete from filesystem (pass user_id for user-specific paths)
        downloader = VideoDownloader(user_id=user_id)
        downloader.delete_video(None, video.title)  # Pass None for file_path since we don't store it
        
        # Delete associated files (flashcards, quizzes, transcripts)
        # Note: downloader.delete_video might try to delete transcripts based on title, 
        # but explicit deletion using stored paths is safer.
        
        for flashcard in video.flashcards:
            if flashcard.file_path:
                if flashcard.file_path.startswith("s3://"):
                    delete_from_s3(flashcard.file_path)
                elif os.path.exists(flashcard.file_path):
                    try:
                        os.remove(flashcard.file_path)
                        print(f"Deleted flashcard file: {flashcard.file_path}")
                    except Exception as e:
                        print(f"Error deleting flashcard file {flashcard.file_path}: {e}")

        for quiz in video.quizzes:
            if quiz.file_path:
                if quiz.file_path.startswith("s3://"):
                    delete_from_s3(quiz.file_path)
                elif os.path.exists(quiz.file_path):
                    try:
                        os.remove(quiz.file_path)
                        print(f"Deleted quiz file: {quiz.file_path}")
                    except Exception as e:
                        print(f"Error deleting quiz file {quiz.file_path}: {e}")

        for transcript in video.transcripts:
            if transcript.file_path:
                if transcript.file_path.startswith("s3://"):
                    delete_from_s3(transcript.file_path)
                elif os.path.exists(transcript.file_path):
                    try:
                        os.remove(transcript.file_path)
                        print(f"Deleted transcript file: {transcript.file_path}")
                    except Exception as e:
                        print(f"Error deleting transcript file {transcript.file_path}: {e}")

        # Delete from database
        db.delete(video)
        db.commit()
        
        return {"message": "Video deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate")
async def translate_video(request: TranslateRequest, db: Session = Depends(get_db)):
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get video from DB
        video = db.query(Video).filter(Video.id == request.video_id, Video.user_id == user.id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get original transcript from database (earliest transcript for this video)
        original_transcript = db.query(Transcript).filter(
            Transcript.video_id == video.id
        ).order_by(Transcript.created_at).first()
        
        if not original_transcript:
            raise HTTPException(status_code=404, detail="Original transcript not found in database")
        
        transcript_path = original_transcript.file_path
        # Perform translation
        # Handle S3 paths
        if transcript_path.startswith("s3://"):
            # Create a temporary local file
            content = read_file_content(transcript_path)
            
            # Create temp directory
            temp_dir = "downloads/temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            filename = os.path.basename(transcript_path)
            temp_input_path = os.path.join(temp_dir, filename)
            
            with open(temp_input_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Translate using local temp file
            translator = Translator()
            # This returns a local path in the same directory as input
            temp_output_path = translator.translate_transcript(temp_input_path, request.target_language)
            
            # Upload result to S3
            if USE_S3:
                output_filename = os.path.basename(temp_output_path)
                s3_key = f"transcripts/{user.email}/{output_filename}"
                translated_path = upload_to_s3(temp_output_path, s3_key)
                
                # Cleanup temp files
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
            else:
                # Should not happen if input was S3, but just in case
                translated_path = temp_output_path
                
        else:
            # Local file path
            if not os.path.exists(transcript_path):
                raise HTTPException(status_code=404, detail=f"Transcript file not found at {transcript_path}")
                
            translator = Translator()
            translated_path = translator.translate_transcript(transcript_path, request.target_language)
            
            # If S3 is enabled but input was local (legacy?), upload result
            if USE_S3:
                output_filename = os.path.basename(translated_path)
                s3_key = f"transcripts/{user.email}/{output_filename}"
                s3_path = upload_to_s3(translated_path, s3_key)
                
                # Cleanup local file
                if os.path.exists(translated_path):
                    os.remove(translated_path)
                
                translated_path = s3_path
        
        # Save translated transcript to database
        # Check if translation already exists
        existing_transcript = db.query(Transcript).filter(
            Transcript.video_id == video.id,
            Transcript.language == request.target_language
        ).first()
        
        if not existing_transcript:
            db_transcript = Transcript(
                video_id=video.id,
                user_id=user.id,
                language=request.target_language,
                file_path=translated_path
            )
            db.add(db_transcript)
            db.commit()
        else:
            # Update existing path
            existing_transcript.file_path = translated_path
            db.commit()
        
        return {
            "message": "Translation successful",
            "original_transcript": transcript_path,
            "translated_transcript": translated_path,
            "language": request.target_language
        }
        
    except Exception as e:
        print(f"Translation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flashcards/generate")
async def generate_flashcards(request: GenerateFlashcardsRequest, db: Session = Depends(get_db)):
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get video from DB
        video = db.query(Video).filter(Video.id == request.video_id, Video.user_id == user.id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
            
        # Get transcript (prefer requested language, fallback to original)
        transcript = db.query(Transcript).filter(
            Transcript.video_id == video.id,
            Transcript.language == request.language
        ).first()
        
        if not transcript:
            # Fallback to any transcript if specific language not found
            # Ideally we should translate first, but for now let's just use what we have
            # or maybe we should error out? The user flow implies they selected a language.
            # Let's try to find the original one.
             transcript = db.query(Transcript).filter(
                Transcript.video_id == video.id
            ).order_by(Transcript.created_at).first()
             
        if not transcript:
             raise HTTPException(status_code=404, detail="No transcript found for this video")

        transcript_path = transcript.file_path
        
        # Read content using helper that handles S3 or local
        try:
            transcript_text = read_file_content(transcript_path)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Could not read transcript file: {e}")

        # Generate flashcards
        generator = FlashcardGenerator()
        flashcards = generator.generate_flashcards(transcript_text, request.language)
        
        # Save to database (optional, but good for caching)
        # For now, just return them
        
        return {"flashcards": [fc.dict() for fc in flashcards]}

    except ValueError as ve:
        raise HTTPException(status_code=500, detail=str(ve))
    except Exception as e:
        print(f"Flashcard generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/flashcards/{flashcard_id}/content")
async def get_flashcard_content(flashcard_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    try:
        # Find user
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
             raise HTTPException(status_code=404, detail="User not found")

        # Find flashcard
        flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_id, Flashcard.user_id == user.id).first()
        if not flashcard:
            raise HTTPException(status_code=404, detail="Flashcard set not found")

        # Read file content
        content = json.loads(read_file_content(flashcard.file_path))

        return {"flashcards": content}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error reading flashcard content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== QUIZ ENDPOINTS ====================

@app.post("/quiz/generate")
async def generate_quiz(request: GenerateQuizRequest, db: Session = Depends(get_db)):
    try:
        # Find user
        user = db.query(User).filter(User.email == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Find video
        video = db.query(Video).filter(Video.id == request.video_id, Video.user_id == user.id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Get transcript for the specified language
        transcript = db.query(Transcript).filter(
            Transcript.video_id == request.video_id,
            Transcript.language == request.language
        ).first()

        if not transcript:
            raise HTTPException(status_code=404, detail=f"No transcript found for language: {request.language}")

        # Read transcript content
        try:
            transcript_text = read_file_content(transcript.file_path)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Could not read transcript file: {e}")

        # Generate quiz using QuizGenerator
        generator = QuizGenerator()
        questions = generator.generate_quiz(transcript_text, request.language)

        # Convert to dict format
        quiz_data = [
            {
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer
            }
            for q in questions
        ]

        return {"quiz": quiz_data}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz/save")
async def save_quiz(request: SaveQuizRequest, db: Session = Depends(get_db)):
    try:
        # 1. Save to File System
        base_dir = "downloads"
        quiz_dir = os.path.join(base_dir, "quizzes", str(request.user_id), str(request.video_id))
        os.makedirs(quiz_dir, exist_ok=True)

        filename = f"quiz_{request.language}.json"
        file_path = os.path.join(quiz_dir, filename)

        # Save to JSON file
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(request.quiz, f, ensure_ascii=False, indent=2)

        # Upload to S3 if enabled
        if USE_S3:
            s3_key = f"quizzes/{request.user_id}/{request.video_id}/{filename}"
            stored_path = upload_to_s3(file_path, s3_key)
            # Optional: Delete local file after upload
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            stored_path = file_path

        # 2. Save to Database
        # Find user
        user = db.query(User).filter(User.email == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Find video
        video = db.query(Video).filter(Video.id == request.video_id, Video.user_id == user.id).first()
        if not video:
             raise HTTPException(status_code=404, detail="Video not found")

        # Check if quiz already exists for this video/language
        existing_quiz = db.query(Quiz).filter(
            Quiz.video_id == video.id,
            Quiz.language == request.language
        ).first()

        if existing_quiz:
            # Update existing
            existing_quiz.file_path = stored_path
            existing_quiz.created_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(existing_quiz)
            print(f"Updated existing quiz for video {video.id} lang {request.language}")
        else:
            # Create new
            new_quiz = Quiz(
                video_id=video.id,
                user_id=user.id,
                language=request.language,
                file_path=stored_path
            )
            db.add(new_quiz)
            db.commit()
            db.refresh(new_quiz)
            print(f"Created new quiz for video {video.id}")

        return {"message": "Quiz saved successfully", "file_path": stored_path}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error saving quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{video_id}/quizzes")
async def get_video_quizzes(video_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    """Get all saved quizzes for a specific video."""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            return {"quizzes": []}
        
        # Verify video belongs to user
        video = db.query(Video).filter(Video.id == video_id, Video.user_id == user.id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get all quizzes for this video
        quizzes = db.query(Quiz).filter(Quiz.video_id == video_id).all()
        
        return {
            "quizzes": [
                {
                    "id": q.id,
                    "language": q.language,
                    "file_path": q.file_path,
                    "created_at": q.created_at
                }
                for q in quizzes
            ]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/{quiz_id}/content")
async def get_quiz_content(quiz_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    try:
        # Find user
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
             raise HTTPException(status_code=404, detail="User not found")

        # Find quiz
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == user.id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Read file content
        content = json.loads(read_file_content(quiz.file_path))

        return {"quiz": content}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error reading quiz content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/flashcards/{flashcard_id}")
async def delete_flashcard(flashcard_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    """Delete a saved flashcard set."""
    try:
        # Find user
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Find flashcard
        flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_id, Flashcard.user_id == user.id).first()
        if not flashcard:
            raise HTTPException(status_code=404, detail="Flashcard set not found")

        # Delete file if exists
        if flashcard.file_path:
            if flashcard.file_path.startswith("s3://"):
                delete_from_s3(flashcard.file_path)
            elif os.path.exists(flashcard.file_path):
                os.remove(flashcard.file_path)
                print(f"Deleted flashcard file: {flashcard.file_path}")

        # Delete from database
        db.delete(flashcard)
        db.commit()
        print(f"Deleted flashcard record with id: {flashcard_id}")

        return {"message": "Flashcard set deleted successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error deleting flashcard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/quiz/{quiz_id}")
async def delete_quiz(quiz_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    """Delete a saved quiz."""
    try:
        # Find user
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Find quiz
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == user.id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Delete file if exists
        if quiz.file_path:
            if quiz.file_path.startswith("s3://"):
                delete_from_s3(quiz.file_path)
            elif os.path.exists(quiz.file_path):
                os.remove(quiz.file_path)
                print(f"Deleted quiz file: {quiz.file_path}")

        # Delete from database
        db.delete(quiz)
        db.commit()
        print(f"Deleted quiz record with id: {quiz_id}")

        return {"message": "Quiz deleted successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error deleting quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
