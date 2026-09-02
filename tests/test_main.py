from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}



def test_create_user():
    response = client.post(
        "/users",
        json={"username": "test_user"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "test_user"
    assert "id" in data