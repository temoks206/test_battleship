from app.fleet import FLEET, generate_fleet, can_place_ship, is_ship_inside_board

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