from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
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

@app.post("/analyze")
async def analyze_video(request: VideoRequest, db: Session = Depends(get_db)):
    try:
        downloader = VideoDownloader()
        # For now, we are just downloading. In the future, we will trigger analysis.
        result = downloader.download_video(request.url)
        
        # Save to database
        db_video = Video(
            user_id=request.user_id,
            title=result['title'],
            file_path=result['filename'],
            url=request.url
        )
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        return {
            "message": "Video downloaded successfully",
            "video": {
                "title": db_video.title,
                "file_path": db_video.file_path,
                "id": db_video.id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # Delete from filesystem
        downloader = VideoDownloader()
        downloader.delete_video(video.file_path)
        
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
