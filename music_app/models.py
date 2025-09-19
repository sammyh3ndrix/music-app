from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from music_app.db import Base


# ---------- USERS ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    # relationships
    uploads = relationship("Upload", back_populates="user")
    likes = relationship("UserLike", back_populates="user")
    history = relationship("UserHistory", back_populates="user")


# ---------- TRACKS ----------
class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    provider = Column(String(50), nullable=False)
    external_id = Column(String(255), unique=True, index=True, nullable=True)
    duration = Column(Integer, nullable=True)

    # relationships
    likes = relationship("UserLike", back_populates="track")
    history = relationship("UserHistory", back_populates="track")


# ---------- UPLOADS ----------
class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    features = Column(Text, nullable=True)  # store JSON/text features (SQLite safe)

    # 🔹 Spotify enrichment fields
    spotify_id = Column(String, nullable=True, index=True)
    spotify_url = Column(String, nullable=True)
    track_name = Column(String, nullable=True)
    artist_name = Column(String, nullable=True)
    album_name = Column(String, nullable=True)
    album_image_url = Column(String, nullable=True)
    popularity = Column(Integer, nullable=True)
    preview_url = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # relationships
    user = relationship("User", back_populates="uploads")


# ---------- USER LIKES ----------
class UserLike(Base):
    __tablename__ = "user_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"))

    # relationships
    user = relationship("User", back_populates="likes")
    track = relationship("Track", back_populates="likes")


# ---------- USER HISTORY ----------
class UserHistory(Base):
    __tablename__ = "user_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"))
    played_at = Column(DateTime, server_default=func.now())

    # relationships
    user = relationship("User", back_populates="history")
    track = relationship("Track", back_populates="history")
