def parse_coordinate(coordinate: str):
    """
    Преобразует координату вида A1-J10
    в пару (row, column).
    """

    if not isinstance(coordinate, str):
        raise ValueError("Координата должна быть строкой")

    coordinate = coordinate.upper()

    if len(coordinate) < 2:
        raise ValueError("Некорректная координата")

    letter = coordinate[0]
    number = coordinate[1:]

    if letter < "A" or letter > "J":
        raise ValueError("Некорректная координата")

    if not number.isdigit():
        raise ValueError("Некорректная координата")

    row_number = int(number)

    if row_number < 1 or row_number > 10:
        raise ValueError("Некорректная координата")

    # Не принимаем, например, A01
    if str(row_number) != number:
        raise ValueError("Некорректная координата")

    row = row_number - 1
    column = ord(letter) - ord("A")

    return row, column


def determine_expected_result(
    fleet,
    coordinate,
    previous_hits,
):
    """
    Арена сама определяет правильный результат выстрела.

    fleet — флот защищающегося игрока из POST /game
    coordinate — текущий выстрел, например D7
    previous_hits — множество предыдущих успешных попаданий
    """

    for ship in fleet:
        ship_coordinates = set(
            ship["coordinates"]
        )

        if coordinate not in ship_coordinates:
            continue

        hits_after_shot = set(previous_hits)
        hits_after_shot.add(coordinate)

        # Если поражены все клетки корабля, правильный ответ — killed
        if ship_coordinates.issubset(hits_after_shot):
            return "killed"

        return "hit"

    return "miss"



EXPECTED_SHIP_LENGTHS = [
    4,
    3, 3,
    2, 2, 2,
    1, 1, 1, 1,
]


def validate_fleet(fleet):
    """
    Проверяет корректность расстановки флота.

    Если флот корректный — возвращает True.
    Если найдено нарушение — вызывает ValueError
    с описанием причины.
    """

    if not isinstance(fleet, list):
        raise ValueError("Флот должен быть списком")

    if len(fleet) != 10:
        raise ValueError(
            "Флот должен содержать 10 кораблей"
        )

    ship_lengths = []
    parsed_ships = []

    # Сначала проверяем каждый корабль отдельно
    for ship in fleet:
        if not isinstance(ship, dict):
            raise ValueError(
                "Некорректное описание корабля"
            )

        if "coordinates" not in ship:
            raise ValueError(
                'У корабля отсутствуют "coordinates"'
            )

        coordinates = ship["coordinates"]

        if not isinstance(coordinates, list):
            raise ValueError(
                '"coordinates" должен быть списком'
            )

        if len(coordinates) == 0:
            raise ValueError(
                "Корабль не может быть пустым"
            )

        ship_lengths.append(
            len(coordinates)
        )

        parsed_coordinates = [
            parse_coordinate(coordinate)
            for coordinate in coordinates
        ]

        # Внутри одного корабля не должно быть повторяющихся клеток
        if len(set(parsed_coordinates)) != len(
            parsed_coordinates
        ):
            raise ValueError(
                "В корабле повторяются координаты"
            )

        rows = {
            row
            for row, column in parsed_coordinates
        }

        columns = {
            column
            for row, column in parsed_coordinates
        }

        # Корабль должен быть расположен либо горизонтально, либо вертикально
        if len(rows) != 1 and len(columns) != 1:
            raise ValueError(
                "Корабль расположен не по прямой"
            )

        # Проверяем отсутствие разрывов
        if len(rows) == 1:
            positions = sorted(
                column
                for row, column in parsed_coordinates
            )
        else:
            positions = sorted(
                row
                for row, column in parsed_coordinates
            )

        expected_positions = list(
            range(
                positions[0],
                positions[0] + len(positions),
            )
        )

        if positions != expected_positions:
            raise ValueError(
                "В корабле есть разрыв между клетками"
            )

        parsed_ships.append(
            set(parsed_coordinates)
        )

    # Проверяем правильное количество кораблей каждого размера
    if sorted(ship_lengths) != sorted(
        EXPECTED_SHIP_LENGTHS
    ):
        raise ValueError(
            "Некорректный состав флота"
        )

    # Проверяем пересечения кораблей
    all_cells = set()

    for ship in parsed_ships:
        if all_cells.intersection(ship):
            raise ValueError(
                "Корабли пересекаются"
            )

        all_cells.update(ship)

    # Проверяем соприкосновение кораблей
    # Корабли не могут касаться даже по диагонали
    for first_index, first_ship in enumerate(
        parsed_ships
    ):
        for second_index, second_ship in enumerate(
            parsed_ships
        ):
            if first_index >= second_index:
                continue

            for row_1, column_1 in first_ship:
                for row_2, column_2 in second_ship:

                    row_distance = abs(
                        row_1 - row_2
                    )

                    column_distance = abs(
                        column_1 - column_2
                    )

                    if (
                        row_distance <= 1
                        and column_distance <= 1
                    ):
                        raise ValueError(
                            "Корабли соприкасаются"
                        )

    return True