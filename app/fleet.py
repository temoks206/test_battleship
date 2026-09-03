import random


BOARD_ROWS = 10
BOARD_COLUMNS = 10

FLEET = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]


def create_ship(start_row, start_column, length, direction):
    ship = []

    for i in range(length):
        if direction == "horizontal":
            ship.append((start_row, start_column + i))
        else:
            ship.append((start_row + i, start_column))

    return ship


def is_ship_inside_board(ship):
    for row, column in ship:
        if row < 0 or row >= BOARD_ROWS:
            return False

        if column < 0 or column >= BOARD_COLUMNS:
            return False

    return True



def can_place_ship(ship, occupied):
    for row, column in ship:
        for row_offset in (-1, 0, 1):
            for column_offset in (-1, 0, 1):
                neighbor = (
                    row + row_offset,
                    column + column_offset,
                )

                if neighbor in occupied:
                    return False

    return True



def generate_ship(length, occupied):
    for _ in range(1000):
        row = random.randrange(BOARD_ROWS)
        column = random.randrange(BOARD_COLUMNS)
        direction = random.choice(["horizontal", "vertical"])

        ship = create_ship(row, column, length, direction)

        if not is_ship_inside_board(ship):
            continue

        if not can_place_ship(ship, occupied):
            continue

        return ship

    raise ValueError("Не удалось разместить корабль")



def generate_fleet():
    fleet = []
    occupied = set()


    for length in FLEET:
        ship = generate_ship(length, occupied)
        fleet.append(ship)
        occupied.update(ship)

    return fleet