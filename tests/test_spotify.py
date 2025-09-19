# tests/test_spotify.py
import io
import pytest

def test_spotify_search(client, monkeypatch):
    """Test /spotify/search returns mapped fields."""

    # Mock Spotify client search
    class DummySpotify:
        def search(self, q, type, limit):
            return {
                "tracks": {
                    "items": [
                        {
                            "id": "123",
                            "name": "Mock Song",
                            "artists": [{"name": "Mock Artist"}],
                            "album": {"name": "Mock Album", "images": [{"url": "http://mock.image"}]},
                            "popularity": 42,
                            "preview_url": "http://mock.preview",
                            "external_urls": {"spotify": "http://mock.spotify"},
                            "duration_ms": 180000,
                        }
                    ]
                }
            }

    monkeypatch.setattr("music_app.utils.spotify.get_spotify_client", lambda: DummySpotify())

    r = client.get("/spotify/search?q=drake&limit=1")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "123"
    assert data[0]["name"] == "Mock Song"
    assert data[0]["artist"] == "Mock Artist"
    assert data[0]["album"] == "Mock Album"
    assert data[0]["album_image_url"] == "http://mock.image"
    assert data[0]["popularity"] == 42
    assert data[0]["preview_url"] == "http://mock.preview"
    assert data[0]["spotify_url"] == "http://mock.spotify"
    assert data[0]["duration_ms"] == 180000


def test_link_upload_to_spotify(client, db_session, monkeypatch):
    """Test linking an upload to a Spotify track."""

    # create user
    r_user = client.post(
        "/users/create",
        json={"email": "spotify_linker@example.com", "password": "testpass123"}
    )
    user_id = r_user.json()["id"]

    # upload dummy file
    fake_file = io.BytesIO(b"fake audio data")
    r_upload = client.post(
        f"/uploads/?user_id={user_id}",
        files={"file": ("demo.mp3", fake_file, "audio/mpeg")}
    )
    upload_id = r_upload.json()["id"]

    # Mock Spotify client track
    class DummySpotify:
        def track(self, spotify_id):
            return {
                "id": spotify_id,
                "name": "Linked Song",
                "artists": [{"name": "Link Artist"}],
                "album": {"name": "Link Album", "images": [{"url": "http://link.image"}]},
                "popularity": 55,
                "preview_url": "http://link.preview",
                "external_urls": {"spotify": "http://link.spotify"},
                "duration_ms": 200000,
            }

    monkeypatch.setattr("music_app.utils.spotify.get_spotify_client", lambda: DummySpotify())

    # link upload to mock Spotify track
    track_id = "mock123"
    r_link = client.post(f"/uploads/{upload_id}/link_spotify?spotify_track_id={track_id}")
    assert r_link.status_code == 200
    data = r_link.json()
    assert data["upload_id"] == upload_id
    assert data["spotify"]["id"] == track_id
    assert data["spotify"]["name"] == "Linked Song"
    assert data["spotify"]["artist"] == "Link Artist"
    assert data["spotify"]["album"] == "Link Album"
