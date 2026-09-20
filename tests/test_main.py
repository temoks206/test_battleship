import uuid
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import GameSession


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}




def test_create_game():
    response = client.post("/game")

    assert response.status_code == 201

    data = response.json()

    assert "session_id" in data
    assert "ships" in data

    uuid.UUID(data["session_id"])

    assert len(data["ships"]) == 10

    for ship in data["ships"]:
        assert "coordinates" in ship

        assert len(ship["coordinates"]) >= 1

        for coordinate in ship["coordinates"]:
            assert isinstance(coordinate, str)

    session = SessionLocal()

    game = session.query(GameSession).filter(
        GameSession.session_id == uuid.UUID(data["session_id"])
    ).first()

    assert game is not None

    session.close()