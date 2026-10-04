from copy import deepcopy

import pytest

from arena.client import ServiceTimeoutError
from arena.match import Match, PlayerServiceError


VALID_FLEET = [
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


class FakeClient:
    """
    Простой тестовый клиент.

    Он позволяет проверить Match.py без запуска настоящего HTTP-сервиса.
    """

    def __init__(
        self,
        game=None,
        shot="A1",
        result="miss",
        opponent_error=None,
    ):
        self.game = game
        self.shot = shot
        self.result = result
        self.opponent_error = opponent_error

    def create_game(self):
        return deepcopy(self.game)

    def make_shot(self, session_id):
        return self.shot

    def opponent_shot(
        self,
        session_id,
        coordinate,
    ):
        if self.opponent_error is not None:
            raise self.opponent_error

        return self.result

    def send_shot_result(
        self,
        session_id,
        result,
    ):
        return {"status": "accepted"}

    def close_game(self, session_id):
        return {"status": "closed"}

    def close(self):
        pass


def make_match():
   
    #Создаёт Match без выполнения реальных HTTP-запросов.
   

    match = Match(
        "http://service-a",
        "http://service-b",
    )

    # Закрываем реальные httpx.Client, созданные конструктором Match.
    match.player_a.close()
    match.player_b.close()

    return match


def test_honest_match_finishes_with_winner(monkeypatch):
    match = make_match()

    match.player_a = FakeClient()
    match.player_b = FakeClient()

    def fake_create_sessions():
        match.session_a = "session-a"
        match.session_b = "session-b"

        match.fleet_a = deepcopy(VALID_FLEET)
        match.fleet_b = deepcopy(VALID_FLEET)

    def fake_make_turn(**kwargs):
        return (
            "A1",
            "killed",
            "killed",
            True,
            True,
        )

    match.create_sessions = fake_create_sessions
    match.make_turn = fake_make_turn

    # Для теста фиксируем первого игрока.
    monkeypatch.setattr(
        "arena.match.random.choice",
        lambda players: "A",
    )

    winner = match.play()

    assert winner == "A"


def test_invalid_fleet_causes_technical_loss():
    match = make_match()

    valid_game = {
        "session_id": "session-a",
        "ships": deepcopy(VALID_FLEET),
    }

    invalid_fleet = deepcopy(VALID_FLEET)
    invalid_fleet.pop()

    invalid_game = {
        "session_id": "session-b",
        "ships": invalid_fleet,
    }

    match.player_a = FakeClient(
        game=valid_game
    )

    match.player_b = FakeClient(
        game=invalid_game
    )

    with pytest.raises(
        PlayerServiceError
    ) as error:
        match.create_sessions()

    assert error.value.player_name == "B"
    assert (
        "некорректная расстановка флота"
        in error.value.reason
    )


def test_false_result_is_detected():
    match = make_match()

    shooter = FakeClient(
        shot="A1"
    )

    # В A1 находится однопалубный корабль, но защищающийся сервис врёт и говорит miss.
    defender = FakeClient(
        result="miss"
    )

    (
        coordinate,
        result,
        expected_result,
        game_over,
        is_honest,
    ) = match.make_turn(
        shooter=shooter,
        shooter_name="A",
        shooter_session="session-a",
        shooter_shots=set(),
        defender=defender,
        defender_name="B",
        defender_session="session-b",
        defender_fleet=[
            {"coordinates": ["A1"]}
        ],
        defender_hits=set(),
    )

    assert coordinate == "A1"
    assert result == "miss"
    assert expected_result == "killed"
    assert is_honest is False
    assert game_over is False


def test_timeout_is_attributed_to_defender():
    match = make_match()

    shooter = FakeClient(
        shot="A1"
    )

    defender = FakeClient(
        opponent_error=ServiceTimeoutError(
            "сервис не ответил за 1.0 секунду"
        )
    )

    with pytest.raises(
        PlayerServiceError
    ) as error:
        match.make_turn(
            shooter=shooter,
            shooter_name="A",
            shooter_session="session-a",
            shooter_shots=set(),
            defender=defender,
            defender_name="B",
            defender_session="session-b",
            defender_fleet=deepcopy(VALID_FLEET),
            defender_hits=set(),
        )

    assert error.value.player_name == "B"
    assert "1.0 секунду" in error.value.reason


def test_invalid_coordinate_causes_technical_loss():
    match = make_match()

    shooter = FakeClient(
        shot="Z99"
    )

    defender = FakeClient()

    with pytest.raises(
        PlayerServiceError
    ) as error:
        match.make_turn(
            shooter=shooter,
            shooter_name="A",
            shooter_session="session-a",
            shooter_shots=set(),
            defender=defender,
            defender_name="B",
            defender_session="session-b",
            defender_fleet=deepcopy(VALID_FLEET),
            defender_hits=set(),
        )

    assert error.value.player_name == "A"
    assert (
        "недопустимую координату"
        in error.value.reason
    )


def test_repeated_shot_causes_technical_loss():
    match = make_match()

    shooter = FakeClient(
        shot="A1"
    )

    defender = FakeClient()

    previous_shots = {
        "A1"
    }

    with pytest.raises(
        PlayerServiceError
    ) as error:
        match.make_turn(
            shooter=shooter,
            shooter_name="B",
            shooter_session="session-b",
            shooter_shots=previous_shots,
            defender=defender,
            defender_name="A",
            defender_session="session-a",
            defender_fleet=deepcopy(VALID_FLEET),
            defender_hits=set(),
        )

    assert error.value.player_name == "B"
    assert (
        "повторно выстрелил"
        in error.value.reason
    )