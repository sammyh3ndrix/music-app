def test_add_track(client):
    response = client.post("/tracks/add", params={
        "title": "Test Track",
        "artist": "Test Artist",
        "album": "Test Album",
        "provider": "local",
        "external_id": "abc123",
        "duration": 180
    })
    assert response.status_code in [200, 201]
    data = response.json()
    assert "id" in data
