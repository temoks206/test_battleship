from fastapi import FastAPI, HTTPException
from app.database import engine
from sqlalchemy import select

from pydantic import BaseModel
from app.database import SessionLocal



import uuid
from app.models import User, GameSession, Shot
from app.fleet import generate_fleet, fleet_to_contract, coordinate_to_string
from app.game_logic import parse_coordinate, determine_shot_result, choose_next_shot, can_make_shot

class UserCreate(BaseModel):
    username: str


class OpponentShotRequest(BaseModel):
    coordinate: str


class ShotResultRequest(BaseModel):
    result: str


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
                detail="Сессия не найдена",
            )

        # Ищем игровую сессию в базе
        game = session.query(GameSession).filter(
            GameSession.session_id == session_uuid
        ).first()

        if game is None:
            raise HTTPException(
                status_code=404,
                detail="Сессия не найдена",
            )

        # Завершённую игру использовать нельзя
        if game.status == "closed":
            raise HTTPException(
                status_code=410,
                detail="Сессия завершена",
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



@app.post("/game/{session_id}/shot")
def make_shot(session_id: str):
    session = SessionLocal()

    try:
        # Проверяем session_id и приводим его к UUID
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail="Сессия не найдена",
            )

        # Ищем игровую сессию
        game = session.query(GameSession).filter(
            GameSession.session_id == session_uuid
        ).first()

        if game is None:
            raise HTTPException(
                status_code=404,
                detail="Сессия не найдена",
            )

        # Завершённую игру использовать нельзя
        if game.status == "closed":
            raise HTTPException(
                status_code=410,
                detail="Сессия завершена",
            )

        # Получаем ВСЮ историю выстрелов этой игры
        all_shots = session.query(Shot).filter(
            Shot.game_session_id == game.id,
        ).order_by(Shot.id).all()

        # Для проверки очередности нам нужны только сторона и результат каждого выстрела
        game_history = [
            {
                "side": shot.side,
                "result": shot.result,
            }
            for shot in all_shots
        ]

        # Проверяем, разрешён ли сейчас наш выстрел
        if not can_make_shot(game_history):
            raise HTTPException(
                status_code=409,
                detail="Выстрел не в свой ход",
            )

        # Для выбора координаты нам уже нужны только НАШИ предыдущие выстрелы
        self_shots = [
            shot
            for shot in all_shots
            if shot.side == "self"
        ]

        # Приводим наши выстрелы к формату, который понимает choose_next_shot
        shot_history = [
            {
                "row": shot.row,
                "column": shot.column,
                "result": shot.result,
            }
            for shot in self_shots
        ]

        # Выбираем следующую клетку
        coordinate = choose_next_shot(shot_history)

        if coordinate is None:
            raise HTTPException(
                status_code=500,
                detail="Непредвиденная ошибка",
            )

        row, column = coordinate

        # Сохраняем наш новый выстрел пока None, потому что Арена ещё не сообщила результат
        new_shot = Shot(
            game_session_id=game.id,
            side="self",
            row=row,
            column=column,
            result=None,
        )

        session.add(new_shot)
        session.commit()

        # Возвращаем координату в формате API
        return {
            "coordinate": coordinate_to_string(row, column),
        }

    finally:
        session.close()



@app.post("/game/{session_id}/shot/result")
def accept_shot_result(
    session_id: str,
    result_request: ShotResultRequest,
):
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

        # Ищем игровую сессию
        game = session.query(GameSession).filter(
            GameSession.session_id == session_uuid
        ).first()

        if game is None:
            raise HTTPException(
                status_code=404,
                detail="Сессия не найдена",
            )

        # Завершённую игру использовать нельзя
        if game.status == "closed":
            raise HTTPException(
                status_code=410,
                detail="Сессия завершена",
            )

        # Проверяем результат выстрела
        if result_request.result not in (
            "miss",
            "hit",
            "killed",
        ):
            raise HTTPException(
                status_code=400,
                detail="Некорректные данные запроса",
            )

        # Ищем наш выстрел, результат которого ещё не был получен
        pending_shot = session.query(Shot).filter(
            Shot.game_session_id == game.id,
            Shot.side == "self",
            Shot.result.is_(None),
        ).order_by(Shot.id.desc()).first()

        # Если такого выстрела нет, то нарушена последовательность запросов
        if pending_shot is None:
            raise HTTPException(
                status_code=409,
                detail="Нарушена последовательность игры",
            )

        # Сохраняем результат выстрела
        pending_shot.result = result_request.result

        session.commit()

        return {
            "status": "accepted",
        }

    finally:
        session.close()