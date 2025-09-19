import io

# ---------- TRACKS ----------
def test_add_track_success(test_client):
    response = test_client.post("/tracks/add", params={
        "title": "Test Track",
        "artist": "Test Artist",
        "album": "Test Album",
        "provider": "local",
        "external_id": "abc123",
        "duration": 180
    })
    assert response.status_code in [200, 201]


# ---------- UPLOADS ----------
def test_create_upload_success(test_client, test_user):
    fake_file = io.BytesIO(b"fake mp3 data")
    response = test_client.post(
        f"/uploads?user_id={test_user['id']}",  # use real user id
        files={"file": ("demo.mp3", fake_file, "audio/mpeg")}
    )
    assert response.status_code in [200, 201]


# ---------- USERS ----------
def test_create_user_success(test_client):
    import uuid
    unique_email = f"pytest_{uuid.uuid4().hex[:6]}@example.com"
    response = test_client.post("/users/create", params={"email": unique_email})
    assert response.status_code in [200, 201]
