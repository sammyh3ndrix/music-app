import os
import json
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from music_app.db import get_db
from music_app.models import Upload
from music_app.utils.audio import analyze_file

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/")
def upload_file(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    safe_filename = f"{uuid.uuid4()}_{os.path.basename(file.filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_upload = Upload(filename=safe_filename, user_id=user_id)
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)

    return new_upload

@router.get("/all")
def get_uploads(db: Session = Depends(get_db)):
    return db.query(Upload).all()

@router.get("/{upload_id}")
def get_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload

@router.post("/{upload_id}/analyze")
def analyze_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    features = analyze_file(os.path.join(UPLOAD_DIR, upload.filename))
    
    # Convert dict to JSON string for database storage
    upload.features = json.dumps(features)
    db.commit()
    db.refresh(upload)

    return {"upload_id": upload.id, "features": features}  # Return original dict to client

@router.post("/{upload_id}/link_spotify")
def link_upload_to_spotify(
    upload_id: int, 
    spotify_track_id: str, 
    track_name: str = "Mock Song",
    artist_name: str = "Mock Artist",
    album_name: str = "Mock Album",
    album_image_url: str = "http://mock.image/cover.jpg",
    popularity: int = 42,
    preview_url: str = "http://mock.preview/clip.mp3",
    duration_ms: int = 180000,  # 3 minutes
    db: Session = Depends(get_db)
):
    """Link an upload to a Spotify track ID with optional metadata"""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # Update the upload with all Spotify metadata
    upload.spotify_id = spotify_track_id
    upload.spotify_url = f"http://open.spotify.com/track/{spotify_track_id}"
    upload.track_name = track_name
    upload.artist_name = artist_name
    upload.album_name = album_name
    upload.album_image_url = album_image_url
    upload.popularity = popularity
    upload.preview_url = preview_url
    upload.duration_ms = duration_ms
        
    db.commit()
    db.refresh(upload)
    
    return {
        "upload_id": upload.id,
        "spotify_id": upload.spotify_id,
        "spotify_url": upload.spotify_url,
        "track_name": upload.track_name,
        "artist_name": upload.artist_name,
        "album_name": upload.album_name,
        "album_image_url": upload.album_image_url,
        "popularity": upload.popularity,
        "preview_url": upload.preview_url,
        "duration_ms": upload.duration_ms,
        "message": "Successfully linked upload to Spotify track"
    }

@router.get("/{upload_id}/similar")
def get_similar_uploads(upload_id: int, k: int = 5, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    if not upload.features:
        raise HTTPException(status_code=400, detail="Upload has not been analyzed yet")
    
    # Parse JSON string back to dict for processing
    current_features = json.loads(upload.features)
    
    # Get all other analyzed uploads
    other_uploads = db.query(Upload).filter(
        Upload.id != upload_id,
        Upload.features.isnot(None)
    ).all()
    
    similarities = []
    for other_upload in other_uploads:
        other_features = json.loads(other_upload.features)
        # Simple similarity calculation (you can improve this)
        score = calculate_similarity(current_features, other_features)
        similarities.append({
            "id": other_upload.id,
            "filename": other_upload.filename,
            "score": score
        })
    
    # Sort by similarity score and return top k
    similarities.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "upload_id": upload_id,
        "similar": similarities[:k]
    }

def calculate_similarity(features1: dict, features2: dict) -> float:
    """Simple similarity calculation - you can make this more sophisticated."""
    # For now, just return a random similarity score
    import random
    return random.uniform(0.0, 1.0)