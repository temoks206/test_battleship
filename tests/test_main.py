import uuid
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import GameSession, Shot


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



def test_opponent_shot_miss():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0], [0, 1]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    session_id = str(game.session_id)
    game_id = game.id

    session.close()

    response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "J10"},
    )

    assert response.status_code == 200
    assert response.json() == {"result": "miss"}

    session = SessionLocal()

    shot = session.query(Shot).filter(
        Shot.game_session_id == game_id
    ).first()

    assert shot is not None
    assert shot.side == "opponent"
    assert shot.row == 9
    assert shot.column == 9
    assert shot.result == "miss"

    session.close()


def test_opponent_shot_hit():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0], [0, 1]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "A1"},
    )

    assert response.status_code == 200
    assert response.json() == {"result": "hit"}


def test_opponent_shot_killed():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "A1"},
    )

    assert response.status_code == 200
    assert response.json() == {"result": "killed"}


def test_opponent_shot_invalid_coordinate():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "K11"},
    )

    assert response.status_code == 400


def test_opponent_shot_game_not_found():
    unknown_session_id = str(uuid4())

    response = client.post(
        f"/game/{unknown_session_id}/opponent-shot",
        json={"coordinate": "A1"},
    )

    assert response.status_code == 404


def test_opponent_shot_closed_game():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="closed",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "A1"},
    )

    assert response.status_code == 410



def test_opponent_shot_hit_then_killed():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0], [0, 1]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    session_id = str(game.session_id)

    session.close()

    # Первый выстрел попадает в корабль,
    # но ещё не уничтожает его полностью
    first_response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "A1"},
    )

    assert first_response.status_code == 200
    assert first_response.json() == {"result": "hit"}

    # Второй выстрел поражает последнюю клетку корабля
    second_response = client.post(
        f"/game/{session_id}/opponent-shot",
        json={"coordinate": "B1"},
    )

    assert second_response.status_code == 200
    assert second_response.json() == {"result": "killed"}


def test_make_shot():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    game_id = game.id
    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/shot"
    )

    assert response.status_code == 200

    data = response.json()

    assert "coordinate" in data

    # Проверяем, что выстрел сохранился в базе
    session = SessionLocal()

    shot = session.query(Shot).filter(
        Shot.game_session_id == game_id,
        Shot.side == "self",
    ).first()

    assert shot is not None
    assert shot.result is None

    session.close()


def test_make_shot_game_not_found():
    response = client.post(
        f"/game/{uuid4()}/shot"
    )

    assert response.status_code == 404


def test_make_shot_closed_game():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="closed",
    )

    session.add(game)
    session.commit()

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/shot"
    )

    assert response.status_code == 410


def test_make_shot_not_our_turn():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    # Наш предыдущий выстрел был промахом,
    # значит сейчас должен ходить противник
    shot = Shot(
        game_session_id=game.id,
        side="self",
        row=0,
        column=0,
        result="miss",
    )

    session.add(shot)
    session.commit()

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/shot"
    )

    assert response.status_code == 409


def test_make_shot_after_hit():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    # Предыдущий наш выстрел попал в D7
    shot = Shot(
        game_session_id=game.id,
        side="self",
        row=6,
        column=3,
        result="hit",
    )

    session.add(shot)
    session.commit()

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/shot"
    )

    assert response.status_code == 200

    # После попадания следующий выстрел должен
    # быть по одной из соседних клеток D7
    assert response.json()["coordinate"] in {
        "D6",
        "D8",
        "C7",
        "E7",
    }


def test_make_shot_does_not_repeat():
    session = SessionLocal()

    game = GameSession(
        session_id=uuid4(),
        fleet=[
            [[0, 0]],
        ],
        status="opened",
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    # Ранее мы стреляли в A1 и промахнулись
    self_shot = Shot(
        game_session_id=game.id,
        side="self",
        row=0,
        column=0,
        result="miss",
    )

    # Затем противник тоже промахнулся,
    # поэтому ход снова перешёл к нам
    opponent_shot = Shot(
        game_session_id=game.id,
        side="opponent",
        row=9,
        column=9,
        result="miss",
    )

    session.add(self_shot)
    session.add(opponent_shot)
    session.commit()

    session_id = str(game.session_id)

    session.close()

    response = client.post(
        f"/game/{session_id}/shot"
    )

    assert response.status_code == 200

    # Повторно стрелять в A1 нельзя
    assert response.json()["coordinate"] != "A1"