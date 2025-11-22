from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os
import json
import asyncio
from sqlalchemy.orm import Session

# Add the src directory to the python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from downloader.video_downloader import VideoDownloader
from database import init_db, get_db, Video

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
        
        # Save to database
        from database import SessionLocal
        db = SessionLocal()
        try:
            db_video = Video(
                user_id=user_id,
                title=video_title,
                file_path=video_path,
                url=url
            )
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            
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
        videos = db.query(Video).filter(Video.user_id == user_id).all()
        return {
            "videos": [
                {
                    "id": v.id,
                    "title": v.title,
                    "file_path": v.file_path,
                    "url": v.url,
                    "created_at": v.created_at
                }
                for v in videos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/videos/{video_id}")
async def delete_video(video_id: int, user_id: str = "anonymous", db: Session = Depends(get_db)):
    try:
        video = db.query(Video).filter(Video.id == video_id, Video.user_id == user_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Delete from filesystem (pass user_id for user-specific paths)
        downloader = VideoDownloader(user_id=user_id)
        downloader.delete_video(video.file_path, video.title)
        
        # Delete from database
        db.delete(video)
        db.commit()
        
        return {"message": "Video deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
