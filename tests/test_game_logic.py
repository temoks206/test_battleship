import pytest

from app.game_logic import parse_coordinate, determine_shot_result

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

