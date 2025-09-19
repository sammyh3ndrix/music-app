import os
from dotenv import load_dotenv
from fastapi import FastAPI
from music_app.db import Base, engine
from music_app.routers import users, tracks, uploads, likes
from music_app.routers import spotify
from music_app.routers import recommendations

# Load .env
load_dotenv()

# --- Database init ---
Base.metadata.create_all(bind=engine)

# --- FastAPI app ---
app = FastAPI(title="Music App")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Routers ---
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(tracks.router, prefix="/tracks", tags=["Tracks"])
app.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
app.include_router(likes.router, prefix="/likes", tags=["Likes"])
app.include_router(spotify.router, prefix="/spotify", tags=["Spotify"])
app.include_router(recommendations.router, tags=["Recommendations"])
