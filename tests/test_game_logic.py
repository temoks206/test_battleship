import pytest

from app.game_logic import parse_coordinate, determine_shot_result, get_neighbor_cells, choose_neighbor_shot, choose_random_shot, get_active_hits, choose_next_shot, can_make_shot

def test_parse_coordinate():
    assert parse_coordinate("A1") == (0, 0)
    assert parse_coordinate("D7") == (6, 3)
    assert parse_coordinate("J10") == (9, 9)


def test_parse_coordinate_invalid():
    invalid_coordinates = [
        "A0",
        "A11",
        "K1",
        "1A",
        "A01",
        "ABC",
        "",
    ]

    for coordinate in invalid_coordinates:
        with pytest.raises(ValueError):
            parse_coordinate(coordinate)



def test_shot_result_miss():
    fleet = [
        [[0, 0], [0, 1], [0, 2]],
    ]

    result = determine_shot_result(
        fleet=fleet,
        previous_hits=[],
        coordinate=(5, 5),
    )

    assert result == "miss"


def test_shot_result_hit():
    fleet = [
        [[0, 0], [0, 1], [0, 2]],
    ]

    result = determine_shot_result(
        fleet=fleet,
        previous_hits=[],
        coordinate=(0, 0),
    )

    assert result == "hit"


def test_shot_result_killed():
    fleet = [
        [[0, 0], [0, 1], [0, 2]],
    ]

    result = determine_shot_result(
        fleet=fleet,
        previous_hits=[(0, 0), (0, 1)],
        coordinate=(0, 2),
    )

    assert result == "killed"


def test_shot_result_single_cell_ship_killed():
    fleet = [
        [[4, 4]],
    ]

    result = determine_shot_result(
        fleet=fleet,
        previous_hits=[],
        coordinate=(4, 4),
    )

    assert result == "killed"


def test_repeated_shot_on_killed_ship():
    fleet = [
        [[0, 0], [0, 1], [0, 2]],
    ]

    result = determine_shot_result(
        fleet=fleet,
        previous_hits=[(0, 0), (0, 1), (0, 2)],
        coordinate=(0, 0),
    )

    assert result == "killed"


def test_repeated_shot_on_damaged_ship():
    fleet = [
        [[0, 0], [0, 1], [0, 2]],
    ]

    result = determine_shot_result(
        fleet=fleet,
        previous_hits=[(0, 0)],
        coordinate=(0, 0),
    )

    assert result == "hit"



def test_get_neighbor_cells():
    neighbors = get_neighbor_cells(6, 3)

    assert set(neighbors) == {
        (5, 3),
        (7, 3),
        (6, 2),
        (6, 4),
    }


def test_get_neighbor_cells_on_corner():
    neighbors = get_neighbor_cells(0, 0)

    assert set(neighbors) == {
        (1, 0),
        (0, 1),
    }



def test_get_neighbor_cells():
    neighbors = get_neighbor_cells(6, 3)

    assert set(neighbors) == {
        (5, 3),
        (7, 3),
        (6, 2),
        (6, 4),
    }


def test_get_neighbor_cells_on_corner():
    neighbors = get_neighbor_cells(0, 0)

    assert set(neighbors) == {
        (1, 0),
        (0, 1),
    }


def test_choose_neighbor_shot():
    used_shots = [
        (5, 3),
    ]

    shot = choose_neighbor_shot(
        row=6,
        column=3,
        used_shots=used_shots,
    )

    assert shot in {
        (7, 3),
        (6, 2),
        (6, 4),
    }

    assert shot not in used_shots


def test_choose_neighbor_shot_no_available_cells():
    used_shots = [
        (5, 3),
        (7, 3),
        (6, 2),
        (6, 4),
    ]

    shot = choose_neighbor_shot(
        row=6,
        column=3,
        used_shots=used_shots,
    )

    assert shot is None



def test_choose_random_shot():
    used_shots = [
        (0, 0),
        (0, 1),
        (5, 5),
    ]

    shot = choose_random_shot(used_shots)

    assert shot is not None
    assert shot not in used_shots

    row, column = shot

    assert 0 <= row < 10
    assert 0 <= column < 10


def test_choose_random_shot_no_available_cells():
    used_shots = [
        (row, column)
        for row in range(10)
        for column in range(10)
    ]

    shot = choose_random_shot(used_shots)

    assert shot is None



def test_get_active_hits():
    shots = [
        {"row": 6, "column": 3, "result": "hit"},
        {"row": 5, "column": 3, "result": "miss"},
    ]

    assert get_active_hits(shots) == [
        (6, 3),
    ]


def test_get_active_hits_multiple():
    shots = [
        {"row": 6, "column": 3, "result": "hit"},
        {"row": 6, "column": 4, "result": "hit"},
    ]

    assert get_active_hits(shots) == [
        (6, 3),
        (6, 4),
    ]


def test_get_active_hits_after_killed():
    shots = [
        {"row": 1, "column": 1, "result": "hit"},
        {"row": 1, "column": 2, "result": "killed"},
        {"row": 6, "column": 3, "result": "hit"},
    ]

    assert get_active_hits(shots) == [
        (6, 3),
    ]



def test_choose_next_shot_without_hits():
    shots = [
        {"row": 0, "column": 0, "result": "miss"},
        {"row": 5, "column": 5, "result": "miss"},
    ]

    shot = choose_next_shot(shots)

    assert shot is not None
    assert shot not in {
        (0, 0),
        (5, 5),
    }


def test_choose_next_shot_with_one_hit():
    shots = [
        {"row": 6, "column": 3, "result": "hit"},
    ]

    shot = choose_next_shot(shots)

    # После одного попадания стреляем
    # в одну из соседних клеток
    assert shot in {
        (5, 3),
        (7, 3),
        (6, 2),
        (6, 4),
    }


def test_choose_next_shot_horizontal_ship():
    shots = [
        {"row": 6, "column": 3, "result": "hit"},
        {"row": 6, "column": 4, "result": "hit"},
    ]

    shot = choose_next_shot(shots)

    # Уже понятно, что корабль горизонтальный
    assert shot in {
        (6, 2),
        (6, 5),
    }


def test_choose_next_shot_vertical_ship():
    shots = [
        {"row": 3, "column": 5, "result": "hit"},
        {"row": 4, "column": 5, "result": "hit"},
    ]

    shot = choose_next_shot(shots)

    # Уже понятно, что корабль вертикальный
    assert shot in {
        (2, 5),
        (5, 5),
    }


def test_choose_next_shot_does_not_repeat():
    shots = [
        {"row": 6, "column": 3, "result": "hit"},
        {"row": 5, "column": 3, "result": "miss"},
        {"row": 7, "column": 3, "result": "miss"},
        {"row": 6, "column": 2, "result": "miss"},
    ]

    shot = choose_next_shot(shots)

    # Из четырёх соседей D7 свободным остался только один
    assert shot == (6, 4)



def test_can_make_shot_without_history():
    shots = []

    # История пуста, поэтому сервис не может определить очередность.
    # Если Арена вызвала /shot первой, разрешаем выполнение.
    assert can_make_shot(shots) is True


def test_can_make_shot_while_waiting_result():
    shots = [
        {
            "side": "self",
            "result": None,
        },
    ]

    # Наш выстрел уже сделан, но его результат ещё неизвестен
    assert can_make_shot(shots) is False


def test_can_make_shot_after_our_miss():
    shots = [
        {
            "side": "self",
            "result": "miss",
        },
    ]

    # После нашего промаха ход переходит противнику
    assert can_make_shot(shots) is False


def test_can_make_shot_after_our_hit():
    shots = [
        {
            "side": "self",
            "result": "hit",
        },
    ]

    # После попадания продолжаем стрелять
    assert can_make_shot(shots) is True


def test_can_make_shot_after_our_killed():
    shots = [
        {
            "side": "self",
            "result": "killed",
        },
    ]

    # После уничтожения корабля ход также продолжается
    assert can_make_shot(shots) is True


def test_can_make_shot_after_opponent_miss():
    shots = [
        {
            "side": "opponent",
            "result": "miss",
        },
    ]

    # Противник промахнулся — ход переходит нам
    assert can_make_shot(shots) is True


def test_can_make_shot_after_opponent_hit():
    shots = [
        {
            "side": "opponent",
            "result": "hit",
        },
    ]

    # Противник попал — он продолжает стрелять
    assert can_make_shot(shots) is False


def test_can_make_shot_after_opponent_killed():
    shots = [
        {
            "side": "opponent",
            "result": "killed",
        },
    ]

    # Противник уничтожил корабль — его ход продолжается
    assert can_make_shot(shots) is False



def test_can_make_shot_uses_last_shot():
    shots = [
        {
            "side": "self",
            "result": "miss",
        },
        {
            "side": "opponent",
            "result": "hit",
        },
        {
            "side": "opponent",
            "result": "miss",
        },
    ]

    # Последним был промах противника,
    # поэтому теперь можно стрелять нам
    assert can_make_shot(shots) is True