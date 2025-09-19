def test_create_user(client):
    unique_email = "user_test@example.com"
    response = client.post(
        "/users/create",
        json={"email": unique_email, "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == unique_email
