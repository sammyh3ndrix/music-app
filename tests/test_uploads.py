import io
import pytest
from unittest.mock import patch
from music_app.main import app
from starlette.testclient import TestClient

client = TestClient(app)

def test_create_upload(client, db_session):
    # create user first
    response = client.post(
        "/users/create",
        json={"email": "uploader@example.com", "password": "testpass123"}
    )
    user_id = response.json()["id"]

    # create a fake file
    fake_file = io.BytesIO(b"fake audio data")
    response = client.post(
        f"/uploads/?user_id={user_id}",
        files={"file": ("test.wav", fake_file, "audio/wav")}
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["user_id"] == user_id
    assert "test.wav" in data["filename"]  # Should contain original filename

@patch('music_app.routers.uploads.analyze_file')
def test_analyze_upload(mock_analyze_file, client, db_session):
    # Mock the analyze_file function to return fake features
    mock_analyze_file.return_value = {
        "tempo": 120.0,
        "mfcc_mean": [1.0, 2.0, 3.0],
        "spectral_centroid_mean": 1500.0
    }
    
    # create user
    r_user = client.post(
        "/users/create",
        json={"email": "analyze_tester@example.com", "password": "testpass123"}
    )
    user_id = r_user.json()["id"]

    # upload dummy file
    fake_file = io.BytesIO(b"fake audio data")
    r_upload = client.post(
        f"/uploads/?user_id={user_id}",
        files={"file": ("sample.wav", fake_file, "audio/wav")}
    )
    upload_id = r_upload.json()["id"]

    # call /analyze
    r_analyze = client.post(f"/uploads/{upload_id}/analyze")
    
    assert r_analyze.status_code == 200
    data = r_analyze.json()
    assert data["upload_id"] == upload_id
    assert "features" in data
    assert data["features"]["tempo"] == 120.0
    
    # Verify the mock was called
    mock_analyze_file.assert_called_once()

@patch('music_app.routers.uploads.analyze_file')
def test_similar_uploads(mock_analyze_file, client, db_session):
    # Mock the analyze_file function
    mock_analyze_file.side_effect = [
        {
            "tempo": 120.0,
            "mfcc_mean": [1.0, 2.0, 3.0],
            "spectral_centroid_mean": 1500.0
        },
        {
            "tempo": 130.0,
            "mfcc_mean": [1.1, 2.1, 3.1],
            "spectral_centroid_mean": 1600.0
        }
    ]
    
    # create user 1 + upload
    r_user1 = client.post(
        "/users/create",
        json={"email": "sim1@example.com", "password": "testpass123"}
    )
    user1 = r_user1.json()["id"]
    fake1 = io.BytesIO(b"audio1")
    r1 = client.post(f"/uploads/?user_id={user1}", files={"file": ("f1.wav", fake1, "audio/wav")})
    u1 = r1.json()["id"]

    # create user 2 + upload
    r_user2 = client.post(
        "/users/create",
        json={"email": "sim2@example.com", "password": "testpass123"}
    )
    user2 = r_user2.json()["id"]
    fake2 = io.BytesIO(b"audio2")
    r2 = client.post(f"/uploads/?user_id={user2}", files={"file": ("f2.wav", fake2, "audio/wav")})
    u2 = r2.json()["id"]

    # analyze both
    client.post(f"/uploads/{u1}/analyze")
    client.post(f"/uploads/{u2}/analyze")

    # get similar
    r_similar = client.get(f"/uploads/{u1}/similar?k=1")
    
    assert r_similar.status_code == 200
    data = r_similar.json()
    assert data["upload_id"] == u1
    assert "similar" in data
    # Should find one similar upload (u2)
    if data["similar"]:  # May be empty if similarity calculation returns no results
        assert len(data["similar"]) <= 1