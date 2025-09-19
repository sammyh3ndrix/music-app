from fastapi import APIRouter, Query
from music_app.utils.spotify import search_tracks

router = APIRouter()

@router.get("/search")
def spotify_search(q: str = Query(..., min_length=2), limit: int = 10):
    results = search_tracks(q, limit=limit)
    return {"query": q, "results": results}
