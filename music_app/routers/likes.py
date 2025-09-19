from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from music_app.db import get_db
from music_app.models import User, Track, UserLike

router = APIRouter()

@router.post("/add")
def add_like(user_id: int = Query(...), track_id: int = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    existing = db.query(UserLike).filter_by(user_id=user_id, track_id=track_id).first()
    if existing:
        return {"message": "Already liked"}

    new_like = UserLike(user_id=user_id, track_id=track_id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return {"message": f"User {user_id} liked track {track_id}", "like_id": new_like.id}

@router.delete("/remove")
def remove_like(user_id: int = Query(...), track_id: int = Query(...), db: Session = Depends(get_db)):
    like = db.query(UserLike).filter_by(user_id=user_id, track_id=track_id).first()
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    db.delete(like)
    db.commit()
    return {"message": f"User {user_id} unliked track {track_id}"}

@router.get("/{user_id}")
def list_user_likes(user_id: int, db: Session = Depends(get_db)):
    likes = db.query(UserLike).filter(UserLike.user_id == user_id).all()
    return [
        {
            "id": l.id,
            "track": {
                "id": l.track.id,
                "title": l.track.title,
                "artist": l.track.artist,
                "album": l.track.album,
                "provider": l.track.provider,
            }
        }
        for l in likes
    ]