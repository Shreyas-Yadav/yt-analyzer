from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import os

# Database URL
# Assuming default root user with no password for local development as per plan
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost/yt_analyzer")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    videos = relationship("Video", back_populates="user")
    transcripts = relationship("Transcript", back_populates="user")
    flashcards = relationship("Flashcard", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255))
    url = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="videos")
    transcripts = relationship("Transcript", back_populates="video", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="video")
    quizzes = relationship("Quiz", back_populates="video")

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    language = Column(String(10), nullable=False)  # Language code like 'en', 'es', etc.
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="transcripts")
    user = relationship("User", back_populates="transcripts")

class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    language = Column(String(10), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to JSON file
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="flashcards")
    user = relationship("User", back_populates="flashcards")

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    language = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)  # JSON stored as text
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="quizzes")
    user = relationship("User", back_populates="quizzes")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Create database if it doesn't exist
    # This requires connecting to the server without selecting a DB first
    import sqlalchemy
    from sqlalchemy import text
    
    server_url = DATABASE_URL.rsplit('/', 1)[0]
    db_name = DATABASE_URL.rsplit('/', 1)[1]
    
    # Connect to server to create DB
    temp_engine = create_engine(server_url)
    with temp_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
    
    # Create tables
    Base.metadata.create_all(bind=engine)
