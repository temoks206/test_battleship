from app.fleet import FLEET, generate_fleet, can_place_ship, is_ship_inside_board, coordinate_to_string, fleet_to_contract

# Проверяем чтобы фактический состав флота совпадал с тем который мы задали
def test_fleet_composition():
    fleet = generate_fleet()

    lengths = sorted(len(ship) for ship in fleet)

    assert lengths == sorted(FLEET)



# Проверяем чтобы корабли не были кривыми
def test_straight_ships():
    fleet = generate_fleet()

    for ship in fleet:
        rows = {row for row, column in ship}
        columns = {column for row, column in ship}

        assert len(rows) == 1 or len(columns) == 1



# Проверяем чтобы все корабли не соприкасались друг с другом
def test_ships_do_not_touch():
    fleet = generate_fleet()

    occupied = set()

    for ship in fleet:
        assert can_place_ship(ship, occupied)
        occupied.update(ship)



# Проверяем чтобы корабли не выходили за границу поля
def test_ships_are_inside_board():
    fleet = generate_fleet()

    for ship in fleet:
        assert is_ship_inside_board(ship)



# Проверяем соответствие координат к названию строки
def test_coordinate_to_string():
    assert coordinate_to_string(0, 0) == "A1"
    assert coordinate_to_string(0, 9) == "J1"
    assert coordinate_to_string(4, 4) == "E5"
    assert coordinate_to_string(9, 0) == "A10"
    assert coordinate_to_string(9, 9) == "J10"


# Проверяем формат флота согласно контракту
def test_fleet_to_contract():
    fleet = generate_fleet()

    ships = fleet_to_contract(fleet)

    assert len(ships) == len(FLEET)

    lengths = sorted(len(ship["coordinates"]) for ship in ships)

    assert lengths == sorted(FLEET)

    for ship in ships:
        assert "coordinates" in ship

        for coordinate in ship["coordinates"]:
            assert len(coordinate) in (2, 3)
            assert coordinate[0] in "ABCDEFGHIJ"
            assert 1 <= int(coordinate[1:]) <= 10