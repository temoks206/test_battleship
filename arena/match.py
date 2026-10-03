import random

from arena.client import ServiceClient


class Match:
    def __init__(
        self,
        service_a_url: str,
        service_b_url: str,
    ):
        self.player_a = ServiceClient(service_a_url)
        self.player_b = ServiceClient(service_b_url)

        self.session_a = None
        self.session_b = None

        self.fleet_a = None
        self.fleet_b = None

        # Здесь Арена будет хранить клетки, по которым уже успешно попали
        self.hits_on_a = set()
        self.hits_on_b = set()

        self.winner = None

    def create_sessions(self):
        """Создаёт игровые сессии у обоих сервисов."""

        game_a = self.player_a.create_game()
        game_b = self.player_b.create_game()

        self.session_a = game_a["session_id"]
        self.session_b = game_b["session_id"]

        self.fleet_a = game_a["ships"]
        self.fleet_b = game_b["ships"]

    def get_fleet_cells(self, fleet):
        """Возвращает множество всех клеток флота."""

        cells = set()

        for ship in fleet:
            for coordinate in ship["coordinates"]:
                cells.add(coordinate)

        return cells

    def fleet_is_destroyed(self, fleet, hits):
        """Проверяет, уничтожен ли весь флот."""

        fleet_cells = self.get_fleet_cells(fleet)

        return fleet_cells.issubset(hits)

    def make_turn(
        self,
        shooter,
        shooter_session,
        defender,
        defender_session,
        defender_fleet,
        defender_hits,
    ):
        """
        Выполняет один выстрел.

        Возвращает:
        coordinate — координату выстрела,
        result — miss / hit / killed,
        game_over — уничтожен ли флот защищающегося.
        """

        # Стреляющий сервис выбирает координату
        coordinate = shooter.make_shot(
            shooter_session
        )

        # Передаём этот выстрел защищающемуся сервису
        result = defender.opponent_shot(
            defender_session,
            coordinate,
        )

        # Возвращаем результат стреляющему сервису
        shooter.send_shot_result(
            shooter_session,
            result,
        )

        # Пока считаем сервисы честными.
        # Проверка правдивости будет добавлена в Week 10.
        if result in ("hit", "killed"):
            defender_hits.add(coordinate)

        game_over = self.fleet_is_destroyed(
            defender_fleet,
            defender_hits,
        )

        return coordinate, result, game_over

    def play(self):
        """Проводит полную партию между двумя сервисами."""

        self.create_sessions()

        # Арена сама случайным образом выбирает, кто будет ходить первым
        current_player = random.choice(["A", "B"])

        print(
            f"Первым ходит игрок {current_player}"
        )

        try:
            while self.winner is None:

                if current_player == "A":
                    coordinate, result, game_over = self.make_turn(
                        shooter=self.player_a,
                        shooter_session=self.session_a,
                        defender=self.player_b,
                        defender_session=self.session_b,
                        defender_fleet=self.fleet_b,
                        defender_hits=self.hits_on_b,
                    )

                    print(
                        f"Игрок A стреляет в {coordinate}: {result}"
                    )

                    if game_over:
                        self.winner = "A"
                        break

                    # После промаха ход переходит сопернику
                    if result == "miss":
                        current_player = "B"

                else:
                    coordinate, result, game_over = self.make_turn(
                        shooter=self.player_b,
                        shooter_session=self.session_b,
                        defender=self.player_a,
                        defender_session=self.session_a,
                        defender_fleet=self.fleet_a,
                        defender_hits=self.hits_on_a,
                    )

                    print(
                        f"Игрок B стреляет в {coordinate}: {result}"
                    )

                    if game_over:
                        self.winner = "B"
                        break

                    if result == "miss":
                        current_player = "A"

            print(
                f"\nПобедитель: игрок {self.winner}"
            )

            return self.winner

        finally:
            # После окончания матча закрываем обе сессии
            if self.session_a is not None:
                self.player_a.close_game(
                    self.session_a
                )

            if self.session_b is not None:
                self.player_b.close_game(
                    self.session_b
                )

            self.player_a.close()
            self.player_b.close()