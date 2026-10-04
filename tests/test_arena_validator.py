from copy import deepcopy

import pytest

from arena.validator import validate_fleet


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


def test_valid_fleet():
    assert validate_fleet(VALID_FLEET) is True


def test_invalid_fleet_composition():
    fleet = deepcopy(VALID_FLEET)

    # Превращаем однопалубный корабль в двухпалубный
    # Геометрически корабль корректен, но состав флота теперь неправильный.
    fleet[9]["coordinates"] = ["A7", "A8"]

    with pytest.raises(
        ValueError,
        match="Некорректный состав флота",
    ):
        validate_fleet(fleet)


def test_ship_cannot_be_diagonal():
    fleet = deepcopy(VALID_FLEET)

    fleet[3]["coordinates"] = ["G1", "H2"]

    with pytest.raises(
        ValueError,
        match="Корабль расположен не по прямой",
    ):
        validate_fleet(fleet)


def test_ship_cannot_have_gap():
    fleet = deepcopy(VALID_FLEET)

    fleet[3]["coordinates"] = ["G1", "G3"]

    with pytest.raises(
        ValueError,
        match="В корабле есть разрыв между клетками",
    ):
        validate_fleet(fleet)


def test_ships_cannot_touch():
    fleet = deepcopy(VALID_FLEET)

    # D5 находится рядом с кораблём C5-C6.
    fleet[6]["coordinates"] = ["D5"]

    with pytest.raises(
        ValueError,
        match="Корабли соприкасаются",
    ):
        validate_fleet(fleet)