from concurrent.futures import ThreadPoolExecutor

import pytest
import httpx

from app.database import SessionLocal
from app.models import GameSession, Shot
from time import perf_counter
from uuid import uuid4


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




def test_concurrent_shots_in_same_session():
    # Создаём одну игровую сессию
    response = httpx.post(
        f"{BASE_URL}/game",
        timeout=5.0,
    )

    assert response.status_code == 201

    session_id = response.json()["session_id"]

    # Оба потока будут стрелять в рамках одной и той же игры
    def make_shot():
        return httpx.post(
            f"{BASE_URL}/game/{session_id}/shot",
            timeout=5.0,
        )

    # Отправляем два запроса практически одновременно
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: make_shot(),
                range(2),
            )
        )

    status_codes = sorted(
        response.status_code
        for response in responses
    )

    print(
        f"\nКоды двух параллельных запросов: {status_codes}"
    )

    # Один запрос должен сделать выстрел,
    # второй — получить отказ из-за нарушения очередности
    assert status_codes == [200, 409]





def test_concurrent_results_in_same_session():
    # Создаём игру
    response = httpx.post(
        f"{BASE_URL}/game",
        timeout=5.0,
    )

    assert response.status_code == 201
    session_id = response.json()["session_id"]

    # Сначала сервис делает один выстрел,
    # для которого теперь ожидается результат
    shot_response = httpx.post(
        f"{BASE_URL}/game/{session_id}/shot",
        timeout=5.0,
    )

    assert shot_response.status_code == 200

    # Два потока одновременно пытаются
    # передать результат одного и того же выстрела
    def send_result():
        return httpx.post(
            f"{BASE_URL}/game/{session_id}/shot/result",
            json={
                "result": "miss",
            },
            timeout=5.0,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: send_result(),
                range(2),
            )
        )

    status_codes = sorted(
        response.status_code
        for response in responses
    )

    print(
        f"\nКоды двух параллельных результатов: {status_codes}"
    )

    assert status_codes == [200, 409]





def test_concurrent_close_in_same_session():
    # Создаём одну игровую сессию
    response = httpx.post(
        f"{BASE_URL}/game",
        timeout=5.0,
    )

    assert response.status_code == 201
    session_id = response.json()["session_id"]

    # Два потока одновременно пытаются закрыть одну игру
    def close_game():
        return httpx.post(
            f"{BASE_URL}/game/{session_id}/close",
            timeout=5.0,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: close_game(),
                range(2),
            )
        )

    status_codes = sorted(
        response.status_code
        for response in responses
    )

    print(
        f"\nКоды двух параллельных закрытий: {status_codes}"
    )

    # Один запрос закрывает игру,
    # второй уже видит закрытое состояние
    assert status_codes == [200, 400]




def test_concurrent_opponent_shots_in_same_session():
    # Создаём игру с известным двухпалубным кораблём A1-B1
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

    session_id = str(game.session_id)

    session.close()

    # Одновременно стреляем в обе палубы одного корабля
    coordinates = ["A1", "B1"]

    def send_opponent_shot(coordinate):
        return httpx.post(
            f"{BASE_URL}/game/{session_id}/opponent-shot",
            json={
                "coordinate": coordinate,
            },
            timeout=5.0,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                send_opponent_shot,
                coordinates,
            )
        )

    status_codes = sorted(
        response.status_code
        for response in responses
    )

    results = sorted(
        response.json()["result"]
        for response in responses
    )

    print(
        f"\nКоды параллельных выстрелов противника: {status_codes}"
    )
    print(
        f"Результаты параллельных выстрелов: {results}"
    )

    # Оба выстрела допустимы
    assert status_codes == [200, 200]

    # Первый повреждает корабль, второй уничтожает его
    assert results == ["hit", "killed"]