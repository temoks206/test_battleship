import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="Slow Battleship Service",
)


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


def determine_result(session, coordinate: str):
    
    # Честно определяет результат выстрела по собственному флоту
    

    for ship in FLEET:
        ship_coordinates = set(
            ship["coordinates"]
        )

        if coordinate not in ship_coordinates:
            continue

        session["hits"].add(coordinate)

        if ship_coordinates.issubset(
            session["hits"]
        ):
            return "killed"

        return "hit"

    return "miss"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/game", status_code=201)
def create_game():
    session_id = str(uuid4())

    sessions[session_id] = {
        "shot_index": 0,
        "hits": set(),
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
    session = get_session(session_id)

    # Специально отвечаем дольше допустимой ареной одной секунды
    time.sleep(2)

    result = determine_result(
        session,
        request.coordinate.upper(),
    )

    return {
        "result": result,
    }


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