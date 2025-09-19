# music_app/routers/recommendations.py

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from music_app.db import get_db
from music_app.models import Upload
from music_app.utils.similarity import top_k_similar
from music_app.utils.spotify import cached_track_lookup, search_tracks

router = APIRouter()

# -------------------------------
# Get Recommendations
# -------------------------------
@router.get("/recommendations")
def get_recommendations(
    upload_id: int,
    k: int = 5,
    max_popularity: int = 100,
    page: int = 1,
    per_page: int = 10,
    db: Session = Depends(get_db),
):
    """
    Recommend similar uploads enriched with Spotify metadata.
    Supports popularity filter + pagination.
    """
    # get the target upload
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if not upload.features:
        raise HTTPException(status_code=400, detail="Upload has not been analyzed yet")

    # load features
    target_features = json.loads(upload.features)

    # collect candidate uploads
    candidates = [
        (u.id, json.loads(u.features))
        for u in db.query(Upload)
        .filter(Upload.id != upload_id, Upload.features.isnot(None))
        .all()
    ]
    if not candidates:
        return {
            "upload_id": upload_id,
            "recommendations": [],
            "page": 1,
            "per_page": k,
            "total": 0,
        }

    # compute similarities
    results = top_k_similar(target_features, candidates, k=k)

    # enrich with Spotify
    recs = []
    for uid, score in results:
        candidate = db.query(Upload).filter(Upload.id == uid).first()
        item = {"id": uid, "similarity": score}

        if candidate.spotify_id:
            try:
                item["spotify"] = cached_track_lookup(candidate.spotify_id)
            except Exception:
                item["spotify"] = None

        recs.append(item)

    # filter by popularity if field exists
    recs = [
        r for r in recs
        if not r.get("spotify") or r["spotify"].get("popularity", 0) <= max_popularity
    ]

    # apply pagination
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "upload_id": upload_id,
        "recommendations": recs[start:end],
        "page": page,
        "per_page": per_page,
        "total": len(recs),
    }


# -------------------------------
# Link Upload to Spotify from Search
# -------------------------------
@router.post("/recommendations/link_from_search")
def link_from_search(upload_id: int, query: str, db: Session = Depends(get_db)):
    """Search Spotify and link the first result to an upload."""
    results = search_tracks(query, limit=1)
    if not results:
        raise HTTPException(status_code=404, detail="No track found")

    track = results[0]
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Only set Spotify-related fields
    upload.spotify_id = track["id"]
    upload.spotify_url = track["spotify_url"]
    upload.album_image_url = track["album_image_url"]
    upload.popularity = track["popularity"]
    upload.duration_ms = track["duration_ms"]

    db.commit()
    db.refresh(upload)

    return {"upload_id": upload.id, "spotify": track}
