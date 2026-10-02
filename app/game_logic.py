import random


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


# Выбор клеток при попадании
def get_neighbor_cells(row, column):
    neighbors = [
        (row - 1, column),
        (row + 1, column),
        (row, column - 1),
        (row, column + 1),
    ]

    return [
        (neighbor_row, neighbor_column)
        for neighbor_row, neighbor_column in neighbors
        if 0 <= neighbor_row < 10
        and 0 <= neighbor_column < 10
    ]


# Рандомизируем выбор клеток
def choose_neighbor_shot(row, column, used_shots):
    # Получаем соседние клетки вокруг попадания
    neighbors = get_neighbor_cells(row, column)

    # Приводим уже использованные координаты к единому виду
    used_shots = {
        tuple(shot)
        for shot in used_shots
    }

    # Оставляем только те соседние клетки,
    # по которым мы ещё не стреляли
    available_neighbors = [
        cell
        for cell in neighbors
        if cell not in used_shots
    ]

    # Если свободных соседних клеток не осталось
    if not available_neighbors:
        return None

    # Случайно выбираем одну из доступных клеток
    return random.choice(available_neighbors)



# Случайный выстрел по ещё не использованной клетке
def choose_random_shot(used_shots):
    # Приводим использованные координаты к единому виду
    used_shots = {
        tuple(shot)
        for shot in used_shots
    }

    # Собираем все клетки поля, по которым ещё не стреляли
    available_cells = [
        (row, column)
        for row in range(10)
        for column in range(10)
        if (row, column) not in used_shots
    ]

    # Если свободных клеток больше нет, выбираем случайную свободную клетку
    if not available_cells:
        return None

    return random.choice(available_cells)



# Ищем попадания по кораблю, который ещё не был добит
def get_active_hits(shots):
    active_hits = []

    for shot in shots:
        result = shot["result"]

        if result == "killed":
            active_hits = []

        elif result == "hit":
            active_hits.append(
                (shot["row"], shot["column"])
            )

    return active_hits



# Выбор следующего выстрела
def choose_next_shot(shots):
    # Все клетки, по которым мы уже стреляли
    used_shots = [
        (shot["row"], shot["column"])
        for shot in shots
    ]

    # Получаем попадания по кораблю, который ещё не добит
    active_hits = get_active_hits(shots)

    # Если активных попаданий нет, то выбираем случайную новую клетку
    if not active_hits:
        return choose_random_shot(used_shots)

    # Если пока есть только одно попадание, то проверяем случайную соседнюю клетку
    if len(active_hits) == 1:
        row, column = active_hits[0]

        return choose_neighbor_shot(
            row,
            column,
            used_shots,
        )

    # Если попаданий несколько, то определяем направление корабля
    rows = {
        row
        for row, column in active_hits
    }

    columns = {
        column
        for row, column in active_hits
    }

    possible_shots = []

    # Горизонтальный корабль
    if len(rows) == 1:
        row = active_hits[0][0]

        hit_columns = [
            column
            for _, column in active_hits
        ]

        possible_shots = [
            (row, min(hit_columns) - 1),
            (row, max(hit_columns) + 1),
        ]

    # Вертикальный корабль
    elif len(columns) == 1:
        column = active_hits[0][1]

        hit_rows = [
            row
            for row, _ in active_hits
        ]

        possible_shots = [
            (min(hit_rows) - 1, column),
            (max(hit_rows) + 1, column),
        ]

    used_shots = set(used_shots)

    # Убираем клетки за пределами поля и клетки, по которым уже стреляли
    possible_shots = [
        (row, column)
        for row, column in possible_shots
        if 0 <= row < 10
        and 0 <= column < 10
        and (row, column) not in used_shots
    ]

    # Если можно продолжить корабль по линии - случайно выбираем одну из сторон
    if possible_shots:
        return random.choice(possible_shots)

    # Запасной вариант: ищем свободного соседа рядом с активными попаданиями
    available_neighbors = []

    for row, column in active_hits:
        neighbors = get_neighbor_cells(row, column)

        for cell in neighbors:
            if (
                cell not in used_shots
                and cell not in available_neighbors
            ):
                available_neighbors.append(cell)

    if available_neighbors:
        return random.choice(available_neighbors)

    # Если вокруг добивать больше нечего, то возвращаемся к случайному поиску
    return choose_random_shot(used_shots)



# Проверяем, можем ли мы сейчас стрелять
def can_make_shot(shots):
    # Ждём ручку от арены
    if not shots:
        return True

    # Для определения хода достаточно последнего выстрела
    last_shot = shots[-1]

    side = last_shot["side"]
    result = last_shot["result"]

    # Последний выстрел был наш
    if side == "self":

        # Результат нашего выстрела ещё не получен
        if result is None:
            return False

        # После попадания наш ход продолжается
        if result in ("hit", "killed"):
            return True

        # После промаха ход переходит противнику
        return False

    # Последний выстрел был противника
    if side == "opponent":

        # После промаха противника ход переходит к нам
        if result == "miss":
            return True

        # После hit или killed противник продолжает стрелять
        return False

    return False