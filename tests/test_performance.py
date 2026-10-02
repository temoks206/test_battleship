from concurrent.futures import ThreadPoolExecutor

import pytest
import httpx

from app.database import SessionLocal
from app.models import GameSession, Shot
from time import perf_counter


BASE_URL = "http://localhost:8000"


def check_service():
    try:
        response = httpx.get(
            f"{BASE_URL}/health",
            timeout=1.0,
        )
        return response.status_code == 200
    except httpx.RequestError:
        return False


@pytest.fixture(autouse=True)
def require_running_service():
    if not check_service():
        pytest.skip(
            "Для performance-тестов требуется запущенный сервис"
        )


def test_parallel_games_are_isolated():
    # Создаём 5 независимых игровых сессий
    session_ids = []

    for _ in range(5):
        response = httpx.post(
            f"{BASE_URL}/game",
            timeout=5.0,
        )

        assert response.status_code == 201

        session_ids.append(
            response.json()["session_id"]
        )

    # В каждую игру одновременно отправляем по одному выстрелу противника.
    def send_opponent_shot(session_id):
        return httpx.post(
            f"{BASE_URL}/game/{session_id}/opponent-shot",
            json={
                "coordinate": "A1",
            },
            timeout=5.0,
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(
            executor.map(
                send_opponent_shot,
                session_ids,
            )
        )

    # Все пять запросов должны успешно обработаться
    for response in responses:
        assert response.status_code == 200
        assert response.json()["result"] in (
            "miss",
            "hit",
            "killed",
        )

    # Теперь проверяем непосредственно БД: у каждой игры должен быть ровно один свой Shot.
    session = SessionLocal()

    try:
        for session_id in session_ids:
            game = session.query(GameSession).filter(
                GameSession.session_id == session_id
            ).first()

            assert game is not None

            shots = session.query(Shot).filter(
                Shot.game_session_id == game.id
            ).all()

            assert len(shots) == 1
            assert shots[0].side == "opponent"

    finally:
        session.close()





def test_parallel_requests_under_one_second():
    # Создаём 10 независимых игр
    session_ids = []

    for _ in range(10):
        response = httpx.post(
            f"{BASE_URL}/game",
            timeout=5.0,
        )

        assert response.status_code == 201
        session_ids.append(
            response.json()["session_id"]
        )

    # Отправляем запрос и отдельно измеряем время именно этого HTTP-запроса
    def send_timed_request(session_id):
        start_time = perf_counter()

        response = httpx.post(
            f"{BASE_URL}/game/{session_id}/opponent-shot",
            json={
                "coordinate": "B2",
            },
            timeout=5.0,
        )

        elapsed_time = perf_counter() - start_time

        return response, elapsed_time

    # Все 10 запросов отправляются параллельно
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(
            executor.map(
                send_timed_request,
                session_ids,
            )
        )

    response_times = []

    for response, elapsed_time in results:
        assert response.status_code == 200

        response_times.append(elapsed_time)

        # Каждый отдельный ответ должен уложиться в секунду
        assert elapsed_time < 1.0

    average_time = sum(response_times) / len(response_times)
    max_time = max(response_times)

    print(
        f"\nСреднее время ответа: {average_time:.3f} с"
    )
    print(
        f"Максимальное время ответа: {max_time:.3f} с"
    )