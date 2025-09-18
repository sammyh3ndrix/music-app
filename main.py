import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Load variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Database setup ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Models ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    uploads = relationship("Upload", back_populates="user")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    artist = Column(String(200), nullable=False)
    album = Column(String(200))
    provider = Column(String(50))   # e.g. spotify, apple, soundcloud
    external_id = Column(String(100))  # external provider ID
    duration = Column(Integer)  # seconds
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

from sqlalchemy.dialects.postgresql import JSONB

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    features = Column(JSONB, nullable=True)  # ✅ store analysis results
    user = relationship("User", back_populates="uploads")



# --- Register models explicitly ---
from sqlalchemy import inspect

print("Registering tables...")
print("Known tables before create_all:", Base.metadata.tables.keys())

Base.metadata.create_all(bind=engine)

inspector = inspect(engine)
print("Known tables after create_all:", inspector.get_table_names())


# --- FastAPI app ---
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}
from fastapi import Depends
from sqlalchemy.orm import Session

# --- Dependency: get DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# --- Spotify API setup ---
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

# --- Spotify lookup endpoint ---
@app.get("/tracks/lookup")
def lookup_track(provider: str, id: str):
    if provider == "spotify":
        track = sp.track(id)
        return {
            "title": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "duration_ms": track["duration_ms"],
            "external_url": track["external_urls"]["spotify"]
        }
    else:
        return {"error": "Only Spotify supported for now"}

# --- User endpoint ---
@app.post("/users/create")
def create_user(email: str, db: Session = Depends(get_db)):
    new_user = User(email=email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email}

# --- Track endpoint ---
@app.post("/tracks/add")
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
    return {
        "id": new_track.id,
        "title": new_track.title,
        "artist": new_track.artist,
        "album": new_track.album,
        "provider": new_track.provider,
        "duration": new_track.duration
    }

# --- Upload endpoint ---
@app.post("/uploads/add")
def add_upload(filename: str, user_id: int, db: Session = Depends(get_db)):
    new_upload = Upload(filename=filename, user_id=user_id)
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)
    return {"id": new_upload.id, "filename": new_upload.filename, "user_id": new_upload.user_id}
# --- Get all users ---
@app.get("/users/all")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "created_at": u.created_at} for u in users]

# --- Get all tracks ---
@app.get("/tracks/all")
def get_tracks(db: Session = Depends(get_db)):
    tracks = db.query(Track).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "artist": t.artist,
            "album": t.album,
            "provider": t.provider,
            "duration": t.duration,
            "created_at": t.created_at
        } for t in tracks
    ]

# --- Get all uploads ---
@app.get("/uploads/all")
def get_uploads(db: Session = Depends(get_db)):
    uploads = db.query(Upload).all()
    return [
        {"id": u.id, "filename": u.filename, "user_id": u.user_id, "uploaded_at": u.uploaded_at}
        for u in uploads
    ]

from fastapi import HTTPException

# --- Get user by ID ---
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "created_at": user.created_at}

# --- Get track by ID ---
@app.get("/tracks/{track_id}")
def get_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return {
        "id": track.id,
        "title": track.title,
        "artist": track.artist,
        "album": track.album,
        "provider": track.provider,
        "duration": track.duration,
        "created_at": track.created_at
    }

# --- Get upload by ID ---
@app.get("/uploads/{upload_id}")
def get_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return {
        "id": upload.id,
        "filename": upload.filename,
        "user_id": upload.user_id,
        "uploaded_at": upload.uploaded_at
    }

# --- Update user ---
@app.put("/users/{user_id}")
def update_user(user_id: int, email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.email = email
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "created_at": user.created_at}

# --- Delete user ---
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted"}

# --- Update track ---
@app.put("/tracks/{track_id}")
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
    return {
        "id": track.id,
        "title": track.title,
        "artist": track.artist,
        "album": track.album,
        "provider": track.provider,
        "duration": track.duration
    }

# --- Delete track ---
@app.delete("/tracks/{track_id}")
def delete_track(track_id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    db.delete(track)
    db.commit()
    return {"message": f"Track {track_id} deleted"}

# --- Update upload ---
@app.put("/uploads/{upload_id}")
def update_upload(upload_id: int, filename: str = None, user_id: int = None, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if filename: upload.filename = filename
    if user_id: upload.user_id = user_id
    db.commit()
    db.refresh(upload)
    return {"id": upload.id, "filename": upload.filename, "user_id": upload.user_id}

# --- Delete upload ---
@app.delete("/uploads/{upload_id}")
def delete_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    db.delete(upload)
    db.commit()
    return {"message": f"Upload {upload_id} deleted"}



from seed import seed  # import the seed function

# Only enable reset-db in development mode
if os.getenv("ENV", "dev") == "dev":
    @app.post("/reset-db")
    def reset_db():
        seed()
        return {"message": "✅ Database reset and seeded with demo + random data"}

import shutil
from fastapi import File, UploadFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/uploads")
def upload_file(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    import uuid
    # Generate safe unique filename
    safe_filename = f"{uuid.uuid4()}_{os.path.basename(file.filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create DB record
    new_upload = Upload(filename=safe_filename, user_id=user_id)
    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)

    return {
        "id": new_upload.id,
        "filename": new_upload.filename,
        "user_id": new_upload.user_id,
        "path": file_path
    }

import librosa
import numpy as np
from fastapi import HTTPException

@app.post("/uploads/{upload_id}/analyze")
def analyze_upload(upload_id: int, db: Session = Depends(get_db)):
    # Fetch upload record
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    # ✅ If features already exist, return them without reprocessing
    if upload.features:
        return {"upload_id": upload.id, "filename": upload.filename, "features": upload.features}

    file_path = os.path.join(UPLOAD_DIR, upload.filename)

    # Load audio file
    try:
        y, sr = librosa.load(file_path, sr=None, mono=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading file: {str(e)}")

    # Extract features
    duration = float(librosa.get_duration(y=y, sr=sr))

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = [float(t) for t in librosa.frames_to_time(beat_frames, sr=sr)]

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    key_index = int(np.argmax(chroma_mean))
    key_labels = ['C', 'C#', 'D', 'D#', 'E', 'F',
                  'F#', 'G', 'G#', 'A', 'A#', 'B']
    detected_key = key_labels[key_index]

    spectral_centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    spectral_contrast = float(librosa.feature.spectral_contrast(y=y, sr=sr).mean())
    zcr = float(librosa.feature.zero_crossing_rate(y).mean())
    mfcc = [float(x) for x in librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)]

    rms = float(librosa.feature.rms(y=y).mean())

    # Mood proxies
    energy = float(min(1.0, rms / 0.1))
    danceability = float(min(1.0, tempo / 200.0))
    valence = float(np.clip(0.5 + (spectral_centroid / 5000.0) - (spectral_contrast / 5000.0), 0, 1))
    acousticness = float(1.0 - (spectral_centroid / 5000.0))
    instrumentalness = float(1.0 - zcr)
    liveness = float(np.random.rand())

    features = {
        "duration": duration,
        "tempo_bpm": float(tempo),
        "beat_times": beat_times[:20],
        "key": detected_key,
        "spectral_centroid": spectral_centroid,
        "spectral_contrast": spectral_contrast,
        "zero_crossing_rate": zcr,
        "mfcc": mfcc,
        "rms_energy": rms,
        "energy": energy,
        "danceability": danceability,
        "valence": valence,
        "acousticness": acousticness,
        "instrumentalness": instrumentalness,
        "liveness": liveness
    }

    # ✅ Save to DB
    upload.features = features
    db.commit()
    db.refresh(upload)

    return {"upload_id": upload.id, "filename": upload.filename, "features": upload.features}
