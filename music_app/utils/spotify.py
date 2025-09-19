from functools import lru_cache
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def get_spotify_client():
    auth_manager = SpotifyClientCredentials(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def search_tracks(query: str, limit: int = 10):
    """Search Spotify tracks by text query."""
    sp = get_spotify_client()
    results = sp.search(q=query, type="track", limit=limit)
    return [map_spotify_track(item) for item in results["tracks"]["items"]]


def map_spotify_track(track: dict) -> dict:
    """Normalize Spotify track object into our schema fields."""
    return {
        "id": track.get("id"),
        "name": track.get("name"),
        "artist": ", ".join([a["name"] for a in track.get("artists", [])]),
        "album": track.get("album", {}).get("name"),
        "album_image_url": (
            track.get("album", {}).get("images", [{}])[0].get("url")
            if track.get("album", {}).get("images") else None
        ),
        "popularity": track.get("popularity"),
        "preview_url": track.get("preview_url"),
        "spotify_url": track.get("external_urls", {}).get("spotify"),
        "duration_ms": track.get("duration_ms"),
    }


@lru_cache(maxsize=512)
def cached_track_lookup(track_id: str) -> dict:
    """Fetch and cache Spotify track lookups."""
    sp = get_spotify_client()
    return map_spotify_track(sp.track(track_id))
