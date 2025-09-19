# tests/test_recommendations.py
import io

def test_recommendations_strict_popularity(client, db_session, monkeypatch):
    """Test /recommendations returns no results if max_popularity is too strict."""

    # Mock analyze_file
    fake_features = {"tempo_bpm": 120.0, "mfcc": [0.1] * 13}
    monkeypatch.setattr("music_app.routers.uploads.analyze_file", lambda _: fake_features)

    # Create user + upload
    r_user = client.post("/users/create", json={"email": "pop@example.com", "password": "testpass123"})
    user_id = r_user.json()["id"]

    fake = io.BytesIO(b"fake audio")
    r_upload = client.post(f"/uploads/?user_id={user_id}", files={"file": ("u.mp3", fake, "audio/mpeg")})
    u1 = r_upload.json()["id"]
    client.post(f"/uploads/{u1}/analyze")

    # Link to Spotify mock
    class DummySpotify:
        def track(self, spotify_id):
            return {
                "id": spotify_id,
                "name": "Song",
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album", "images": [{"url": "http://img"}]},
                "popularity": 90,  # too high
                "preview_url": None,
                "external_urls": {"spotify": "http://spotify"},
                "duration_ms": 200000,
            }

    monkeypatch.setattr("music_app.utils.spotify.get_spotify_client", lambda: DummySpotify())
    client.post(f"/uploads/{u1}/link_spotify?spotify_track_id=rec_high")

    # Call recommendations with strict popularity filter
    r_rec = client.get(f"/recommendations?upload_id={u1}&max_popularity=10")
    assert r_rec.status_code == 200
    data = r_rec.json()
    assert data["recommendations"] == []
    assert "page" in data and "per_page" in data and "total" in data


def test_recommendations_respects_k(client, db_session, monkeypatch):
    """Test /recommendations only returns k results."""

    fake_features = {"tempo_bpm": 120.0, "mfcc": [0.1] * 13}
    monkeypatch.setattr("music_app.routers.uploads.analyze_file", lambda _: fake_features)

    # Dummy Spotify
    class DummySpotify:
        def track(self, spotify_id):
            return {
                "id": spotify_id,
                "name": f"Song {spotify_id}",
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album", "images": [{"url": "http://img"}]},
                "popularity": 30,
                "preview_url": None,
                "external_urls": {"spotify": "http://spotify"},
                "duration_ms": 200000,
            }

    monkeypatch.setattr("music_app.utils.spotify.get_spotify_client", lambda: DummySpotify())

    # Create base user + upload
    r_user = client.post("/users/create", json={"email": "kuser@example.com", "password": "testpass123"})
    user_id = r_user.json()["id"]

    fake = io.BytesIO(b"fake audio")
    r_upload = client.post(f"/uploads/?user_id={user_id}", files={"file": ("base.mp3", fake, "audio/mpeg")})
    u_base = r_upload.json()["id"]
    client.post(f"/uploads/{u_base}/analyze")

    # Create multiple uploads
    for i in range(5):
        fake = io.BytesIO(b"fake audio")
        r_upload = client.post(f"/uploads/?user_id={user_id}", files={"file": (f"u{i}.mp3", fake, "audio/mpeg")})
        u_id = r_upload.json()["id"]
        client.post(f"/uploads/{u_id}/analyze")
        client.post(f"/uploads/{u_id}/link_spotify?spotify_track_id=track{i}")

    r_rec = client.get(f"/recommendations?upload_id={u_base}&k=3")
    assert r_rec.status_code == 200
    data = r_rec.json()
    assert len(data["recommendations"]) == 3


def test_recommendations_pagination(client, db_session, monkeypatch):
    """Test /recommendations pagination works correctly."""

    fake_features = {"tempo_bpm": 120.0, "mfcc": [0.1] * 13}
    monkeypatch.setattr("music_app.routers.uploads.analyze_file", lambda _: fake_features)

    class DummySpotify:
        def track(self, spotify_id):
            return {
                "id": spotify_id,
                "name": f"Song {spotify_id}",
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album", "images": [{"url": "http://img"}]},
                "popularity": 20,
                "preview_url": None,
                "external_urls": {"spotify": "http://spotify"},
                "duration_ms": 200000,
            }

    monkeypatch.setattr("music_app.utils.spotify.get_spotify_client", lambda: DummySpotify())

    r_user = client.post("/users/create", json={"email": "pageuser@example.com", "password": "testpass123"})
    user_id = r_user.json()["id"]

    fake = io.BytesIO(b"fake audio")
    r_upload = client.post(f"/uploads/?user_id={user_id}", files={"file": ("base.mp3", fake, "audio/mpeg")})
    u_base = r_upload.json()["id"]
    client.post(f"/uploads/{u_base}/analyze")

    for i in range(6):
        fake = io.BytesIO(b"fake audio")
        r_upload = client.post(f"/uploads/?user_id={user_id}", files={"file": (f"p{i}.mp3", fake, "audio/mpeg")})
        u_id = r_upload.json()["id"]
        client.post(f"/uploads/{u_id}/analyze")
        client.post(f"/uploads/{u_id}/link_spotify?spotify_track_id=p{i}")

    r_page1 = client.get(f"/recommendations?upload_id={u_base}&page=1&per_page=3")
    assert r_page1.status_code == 200
    data1 = r_page1.json()
    assert len(data1["recommendations"]) == 3
    assert data1["page"] == 1

    r_page2 = client.get(f"/recommendations?upload_id={u_base}&page=2&per_page=3")
    assert r_page2.status_code == 200
    data2 = r_page2.json()
    assert len(data2["recommendations"]) == 3 or len(data2["recommendations"]) == 2


def test_link_from_search(client, db_session, monkeypatch):
    """Test linking an upload to Spotify using search query."""

    def fake_search_tracks(query, limit=1):
        return [{
            "id": "search123",
            "name": "Search Song",
            "artist": "Search Artist",
            "album": "Search Album",
            "album_image_url": "http://img",
            "popularity": 40,
            "preview_url": "http://preview",
            "spotify_url": "http://spotify",
            "duration_ms": 180000,
        }]

    monkeypatch.setattr("music_app.routers.recommendations.search_tracks", fake_search_tracks)

    r_user = client.post("/users/create", json={"email": "searchuser@example.com", "password": "testpass123"})
    user_id = r_user.json()["id"]

    fake = io.BytesIO(b"fake audio")
    r_upload = client.post(f"/uploads/?user_id={user_id}", files={"file": ("search.mp3", fake, "audio/mpeg")})
    u_id = r_upload.json()["id"]

    r_link = client.post(f"/recommendations/link_from_search?upload_id={u_id}&query=test")
    assert r_link.status_code == 200
    data = r_link.json()
    assert data["spotify"]["id"] == "search123"
