# Разбор координат
def parse_coordinate(coordinate):

    # Координата должна быть строкой
    if not isinstance(coordinate, str):
        raise ValueError("Некорректная координата")

    # Возможные варианты: A1 ... J9 или A10 ... J10
    if len(coordinate) not in (2, 3):
        raise ValueError("Некорректная координата")

    letter = coordinate[0]
    number = coordinate[1:]

    # Столбцы игрового поля: от A до J
    if letter < "A" or letter > "J":
        raise ValueError("Некорректная координата")

    # После буквы должно быть только число
    if not number.isdigit():
        raise ValueError("Некорректная координата")

    row_number = int(number)

    # Строки игрового поля: от 1 до 10
    if row_number < 1 or row_number > 10:
        raise ValueError("Некорректная координата")

    # Не разрешаем формы вроде A01
    if str(row_number) != number:
        raise ValueError("Некорректная координата")

    row = row_number - 1
    column = ord(letter) - ord("A")

    return row, column


# Определяем результат выстрела
def determine_shot_result(fleet, previous_hits, coordinate):

    # Приводим координату текущего выстрела к единому виду
    coordinate = tuple(coordinate)

    # Предыдущие попадания приводим к кортежам
    hits = {
        tuple(hit)
        for hit in previous_hits
    }

    for ship in fleet:
        # После хранения в JSON координаты могут быть списками
        ship_coordinates = {
            tuple(cell)
            for cell in ship
        }

        # Если выстрел пришёлся по этому кораблю
        if coordinate in ship_coordinates:
            hits_after_shot = hits | {coordinate}

            # Все клетки корабля уже поражены
            if ship_coordinates.issubset(hits_after_shot):
                return "killed"

            return "hit"

    return "miss"