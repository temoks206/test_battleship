from fastapi import FastAPI, HTTPException
from app.database import engine
from sqlalchemy import select

from pydantic import BaseModel
from app.database import SessionLocal



import uuid
from app.models import User, GameSession, Shot
from app.fleet import generate_fleet, fleet_to_contract
from app.game_logic import parse_coordinate, determine_shot_result

class UserCreate(BaseModel):
    username: str


class OpponentShotRequest(BaseModel):
    coordinate: str


app = FastAPI(title="Battleship Service")


@app.get("/health")
def health_check():
    return {"status": "OK"}


@app.post("/users")
def create_user(user: UserCreate):
    session = SessionLocal()

    new_user = User(username=user.username)

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    session.close()

    return {
        "id": new_user.id,
        "username": new_user.username
    }


@app.get("/users")
def get_users():
    session = SessionLocal()

    result = session.execute(select(User))
    users = result.scalars().all()

    session.close()

    return users




@app.post("/game", status_code=201)
def create_game():
    session = SessionLocal()

    session_id = uuid.uuid4()
    fleet = generate_fleet()

    game = GameSession(
        session_id=session_id,
        fleet=fleet,
    )

    session.add(game)
    session.commit()
    session.refresh(game)

    response = {
        "session_id": str(game.session_id),
        "ships": fleet_to_contract(fleet),
    }

    session.close()

    return response


@app.post("/game/{session_id}/opponent-shot")
def opponent_shot(session_id: str, shot_request: OpponentShotRequest):
    session = SessionLocal()

    try:
        # Проверяем session_id и приводим его к UUID
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail="Игровая сессия не найдена",
            )

        # Ищем игровую сессию в базе
        game = session.query(GameSession).filter(
            GameSession.session_id == session_uuid
        ).first()

        if game is None:
            raise HTTPException(
                status_code=404,
                detail="Игровая сессия не найдена",
            )

        # Завершённую игру использовать нельзя
        if game.status == "closed":
            raise HTTPException(
                status_code=410,
                detail="Игровая сессия завершена",
            )

        # Переводим координату вида D7 во внутренний формат
        try:
            row, column = parse_coordinate(shot_request.coordinate)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Некорректная координата",
            )

        # Получаем все предыдущие попадания противника
        previous_hit_shots = session.query(Shot).filter(
            Shot.game_session_id == game.id,
            Shot.side == "opponent",
            Shot.result.in_(["hit", "killed"]),
        ).all()

        previous_hits = [
            (shot.row, shot.column)
            for shot in previous_hit_shots
        ]

        # Определяем результат текущего выстрела
        result = determine_shot_result(
            fleet=game.fleet,
            previous_hits=previous_hits,
            coordinate=(row, column),
        )

        # Сохраняем выстрел противника в историю
        new_shot = Shot(
            game_session_id=game.id,
            side="opponent",
            row=row,
            column=column,
            result=result,
        )

        session.add(new_shot)
        session.commit()

        return {
            "result": result,
        }

    finally:
        session.close()