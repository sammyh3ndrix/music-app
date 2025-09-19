from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from music_app.db import get_db
from music_app.models import Track

router = APIRouter()

@router.post("/add")
def add_track(title: str, artist: str, album: str = None, provider: str = None,
              external_id: str = None, duration: int = None, db: Session = Depends(get_db)):
    new_track = Track(
        title=title,
        artist=artist,
        album=album,
        provider=provider,
        external_id=external_id,
        duration=duration
    )
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track

@router.get("/all")
def get_tracks(db: Session = Depends(get_db)):
    return db.query(Track).all()

@router.get("/{track_id}")
def get_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

@router.put("/{track_id}")
def update_track(track_id: int, title: str = None, artist: str = None, album: str = None,
                 provider: str = None, external_id: str = None, duration: int = None,
                 db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    if title: track.title = title
    if artist: track.artist = artist
    if album: track.album = album
    if provider: track.provider = provider
    if external_id: track.external_id = external_id
    if duration: track.duration = duration
    db.commit()
    db.refresh(track)
    return track

@router.delete("/{track_id}")
def delete_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    db.delete(track)
    db.commit()
    return {"message": f"Track {track_id} deleted"}
