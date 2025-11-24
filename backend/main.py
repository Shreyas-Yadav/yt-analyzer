from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os
import json
import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from downloader.video_downloader import VideoDownloader
from translator.translator import Translator
from generator.flashcard_generator import FlashcardGenerator
from database import init_db, get_db, Video, User, Transcript, Flashcard, Quiz

app = FastAPI()

# Initialize database
init_db()

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

class UserLoginRequest(BaseModel):
    email: str

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
            existing_flashcard.file_path = file_path
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
                file_path=file_path
            )
            db.add(new_flashcard)
            db.commit()
            db.refresh(new_flashcard)
            print(f"Created new flashcards for video {video.id} lang {request.language}")

        return {"message": "Flashcards saved successfully", "path": file_path}

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

async def analyze_video_stream(url: str, user_id: str):
    """Generator function that yields SSE events for each stage"""
    try:
        downloader = VideoDownloader(user_id=user_id)
        
        # Stage 1: Download video
        yield f"data: {json.dumps({'stage': 1, 'message': 'Downloading video...'})}\n\n"
        await asyncio.sleep(0.1)  # Allow event to be sent
        
        result = downloader.download_video(url)
        video_path = result['filename']
        video_title = result['title']
        
        # Stage 2: Extract audio
        yield f"data: {json.dumps({'stage': 2, 'message': 'Extracting audio...'})}\n\n"
        await asyncio.sleep(0.1)
        
        audio_path = downloader.extract_audio(video_path)
        
        # Stage 3: Generate transcript
        yield f"data: {json.dumps({'stage': 3, 'message': 'Generating transcript...'})}\n\n"
        await asyncio.sleep(0.1)
        
        transcript_path = downloader.generate_transcript(audio_path, video_title)
        
        # Cleanup: Delete video and audio files to save storage (keep only transcript)
        print(f"Cleaning up: Deleting video and audio files...")
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"Deleted video: {video_path}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Deleted audio: {audio_path}")
        
        # Save to database
        from database import SessionLocal
        db = SessionLocal()
        try:
            # Find or create user
            user = db.query(User).filter(User.email == user_id).first()
            if not user:
                user = User(email=user_id)
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Create video record
            db_video = Video(
                user_id=user.id,
                title=video_title,
                url=url
            )
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            
            
            # Detect language of the original transcript
            detected_language = 'en'  # Default to English
            try:
                from langdetect import detect
                # Read a sample of the transcript for language detection
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    # Read first 1000 characters for detection
                    sample_text = f.read(1000)
                    # Remove timestamps if present
                    lines = [line.split(']')[-1].strip() if ']' in line else line.strip() 
                            for line in sample_text.split('\n') if line.strip()]
                    text_for_detection = ' '.join(lines[:10])  # Use first 10 lines
                    if text_for_detection:
                        detected_language = detect(text_for_detection)
                        print(f"Detected language: {detected_language}")
            except Exception as e:
                print(f"Language detection failed: {e}, defaulting to 'en'")
            
            # Create transcript record for the original language
            db_transcript = Transcript(
                video_id=db_video.id,
                user_id=user.id,
                language=detected_language,  # Use detected language
                file_path=transcript_path
            )
            db.add(db_transcript)
            db.commit()
            
            # Send completion event
            yield f"data: {json.dumps({'stage': 'complete', 'message': 'Video analyzed successfully!', 'video': {'id': db_video.id, 'title': db_video.title}})}\n\n"
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        yield f"data: {json.dumps({'stage': 'error', 'message': str(e)})}\n\n"

@app.get("/analyze")
async def analyze_video(url: str, user_id: str = "anonymous"):
    return StreamingResponse(
        analyze_video_stream(url, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


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
        if not os.path.exists(transcript_path):
            raise HTTPException(status_code=404, detail=f"Transcript file not found at {transcript_path}")
            
        # Perform translation
        translator = Translator()
        translated_path = translator.translate_transcript(transcript_path, request.target_language)
        
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
        
        return {
            "message": "Translation successful",
            "original_transcript": transcript_path,
            "translated_transcript": translated_path,
            "language": request.target_language
        }
        
    except Exception as e:
        print(f"Translation error: {e}")
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
        if not os.path.exists(transcript_path):
             raise HTTPException(status_code=404, detail=f"Transcript file not found at {transcript_path}")

        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()

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
        if not os.path.exists(flashcard.file_path):
             raise HTTPException(status_code=404, detail="Flashcard file not found on server")

        with open(flashcard.file_path, "r", encoding='utf-8') as f:
            content = json.load(f)

        return {"flashcards": content}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error reading flashcard content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
