from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# Database URL
# Assuming default root user with no password for local development as per plan
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost/yt_analyzer")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    title = Column(String(255))
    file_path = Column(String(255))
    url = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
