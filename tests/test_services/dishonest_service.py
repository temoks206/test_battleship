from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="Dishonest Battleship Service",
)


# Корректный флот
# Он должен успешно пройти validate_fleet() арены
FLEET = [
    {"coordinates": ["A1", "A2", "A3", "A4"]},
    {"coordinates": ["C1", "C2", "C3"]},
    {"coordinates": ["E1", "E2", "E3"]},
    {"coordinates": ["G1", "G2"]},
    {"coordinates": ["I1", "I2"]},
    {"coordinates": ["C5", "C6"]},
    {"coordinates": ["E5"]},
    {"coordinates": ["G5"]},
    {"coordinates": ["I5"]},
    {"coordinates": ["A7"]},
]


FLEET_CELLS = {
    coordinate
    for ship in FLEET
    for coordinate in ship["coordinates"]
}


# Набор координат, которыми нечестный сервис сможет стрелять, если очередь выпадет ему.
SHOT_SEQUENCE = [
    f"{letter}{number}"
    for number in range(1, 11)
    for letter in "ABCDEFGHIJ"
]


sessions = {}


class CoordinateRequest(BaseModel):
    coordinate: str


class ShotResultRequest(BaseModel):
    result: str


def get_session(session_id: str):
    session = sessions.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Сессия не найдена",
        )

    return session


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/game", status_code=201)
def create_game():
    session_id = str(uuid4())

    sessions[session_id] = {
        "shot_index": 0,
        "closed": False,
    }

    return {
        "session_id": session_id,
        "ships": FLEET,
    }


@app.post("/game/{session_id}/shot")
def make_shot(session_id: str):
    session = get_session(session_id)

    index = session["shot_index"]

    coordinate = SHOT_SEQUENCE[
        index % len(SHOT_SEQUENCE)
    ]

    session["shot_index"] += 1

    return {
        "coordinate": coordinate,
    }


@app.post("/game/{session_id}/opponent-shot")
def opponent_shot(
    session_id: str,
    request: CoordinateRequest,
):
    get_session(session_id)

    coordinate = request.coordinate.upper()

    """
     Здесь сервис специально врёт.
    
     Если Арена стреляет в корабль, сервис заявляет miss.
    
     Если Арена стреляет в пустую клетку, сервис заявляет hit.
    
     Поэтому ответ всегда противоречит реальному расположению флота.
    """
    if coordinate in FLEET_CELLS:
        return {"result": "miss"}

    return {"result": "hit"}


@app.post("/game/{session_id}/shot/result")
def accept_shot_result(
    session_id: str,
    request: ShotResultRequest,
):
    get_session(session_id)

    return {
        "status": "accepted",
    }


@app.post("/game/{session_id}/close")
def close_game(session_id: str):
    session = get_session(session_id)

    session["closed"] = True

    return {
        "status": "closed",
    }