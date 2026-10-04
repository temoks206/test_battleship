import random

from arena.client import ServiceClient, ServiceClientError
from arena.validator import validate_fleet, parse_coordinate, determine_expected_result


class PlayerServiceError(Exception):
    def __init__(self, player_name, reason):
        self.player_name = player_name
        self.reason = reason

        super().__init__(
            f"Игрок {player_name}: {reason}"
        )


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

        # Здесь Арена будет хранить клетки, по которым уже успешно попали и отдельно куда вообще стреляли
        self.hits_on_a = set()
        self.hits_on_b = set()

        self.shots_by_a = set()
        self.shots_by_b = set()

        self.winner = None

    def create_sessions(self):
        try:
            game_a = self.player_a.create_game()
        except ServiceClientError as error:
            raise PlayerServiceError(
                "A",
                str(error),
            ) from error

        # Сохраняем данные A сразу.
        self.session_a = game_a["session_id"]
        self.fleet_a = game_a["ships"]

        try:
            validate_fleet(self.fleet_a)
        except ValueError as error:
            raise PlayerServiceError(
                "A",
                f"некорректная расстановка флота: {error}",
            ) from None

        try:
            game_b = self.player_b.create_game()
        except ServiceClientError as error:
            raise PlayerServiceError(
                "B",
                str(error),
            ) from error

        self.session_b = game_b["session_id"]
        self.fleet_b = game_b["ships"]

        try:
            validate_fleet(self.fleet_b)
        except ValueError as error:
            raise PlayerServiceError(
                "B",
                f"некорректная расстановка флота: {error}",
            ) from None

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
        shooter_name,
        shooter_session,
        shooter_shots,
        defender,
        defender_name,
        defender_session,
        defender_fleet,
        defender_hits,
    ):
        try:
            coordinate = shooter.make_shot(
                shooter_session
            )
        except ServiceClientError as error:
            raise PlayerServiceError(
                shooter_name,
                str(error),
            ) from error

        try:
            parse_coordinate(coordinate)
        except ValueError:
            raise PlayerServiceError(
                shooter_name,
                f"сервис вернул недопустимую координату {coordinate}",
            ) from None

        # Приводим координату к единому виду( например, a1 и A1 должны считаться одной клеткой)
        coordinate = coordinate.upper()

        if coordinate in shooter_shots:
            raise PlayerServiceError(
                shooter_name,
                f"сервис повторно выстрелил в клетку {coordinate}",
            )

        shooter_shots.add(coordinate)

        try:
            result = defender.opponent_shot(
                defender_session,
                coordinate,
            )
        except ServiceClientError as error:
            raise PlayerServiceError(
                defender_name,
                str(error),
            ) from error

        # Арена независимо вычисляет, каким результат должен быть на самом деле
        expected_result = determine_expected_result(
            defender_fleet,
            coordinate,
            defender_hits,
        )

        # Если сервис сообщил неправильный результат, матч должен завершиться техническим поражением
        if result != expected_result:
            return (
                coordinate,
                result,
                expected_result,
                False,
                False,
            )

        # Только после проверки честности передаём результат атакующему сервису
        try:
            shooter.send_shot_result(
                shooter_session,
                result,
            )
        except ServiceClientError as error:
            raise PlayerServiceError(
                shooter_name,
                str(error),
            ) from error

        # Арена самостоятельно ведёт историю попаданий
        if expected_result in ("hit", "killed"):
            defender_hits.add(coordinate)

        game_over = self.fleet_is_destroyed(
            defender_fleet,
            defender_hits,
        )

        return (
            coordinate,
            result,
            expected_result,
            game_over,
            True,
        )

    def play(self):
        try:
            try:
                self.create_sessions()

                current_player = random.choice(["A", "B"])
                print(f"Первым ходит игрок {current_player}")

                while self.winner is None:
                    if current_player == "A":
                        (
                            coordinate,
                            result,
                            expected_result,
                            game_over,
                            is_honest,
                        ) = self.make_turn(
                            shooter=self.player_a,
                            shooter_name="A",
                            shooter_session=self.session_a,
                            shooter_shots=self.shots_by_a,
                            defender=self.player_b,
                            defender_name="B",
                            defender_session=self.session_b,
                            defender_fleet=self.fleet_b,
                            defender_hits=self.hits_on_b,
                        )

                        if not is_honest:
                            print(
                                f"Игрок B сообщил ложный результат "
                                f"для выстрела {coordinate}: "
                                f"получено {result}, "
                                f"ожидалось {expected_result}"
                            )

                            self.winner = "A"

                            print(
                                "\nИгрок B получает техническое поражение"
                            )

                            break

                        print(
                            f"Игрок A стреляет в {coordinate}: {result}"
                        )

                        if game_over:
                            self.winner = "A"
                            break

                        if result == "miss":
                            current_player = "B"

                    else:
                        (
                            coordinate,
                            result,
                            expected_result,
                            game_over,
                            is_honest,
                        ) = self.make_turn(
                            shooter=self.player_b,
                            shooter_name="B",
                            shooter_session=self.session_b,
                            shooter_shots=self.shots_by_b,
                            defender=self.player_a,
                            defender_name="A",
                            defender_session=self.session_a,
                            defender_fleet=self.fleet_a,
                            defender_hits=self.hits_on_a,
                        )

                        if not is_honest:
                            print(
                                f"Игрок A сообщил ложный результат "
                                f"для выстрела {coordinate}: "
                                f"получено {result}, "
                                f"ожидалось {expected_result}"
                            )

                            self.winner = "B"

                            print(
                                "\nИгрок A получает техническое поражение"
                            )

                            break

                        print(
                            f"Игрок B стреляет в {coordinate}: {result}"
                        )

                        if game_over:
                            self.winner = "B"
                            break

                        if result == "miss":
                            current_player = "A"

            except PlayerServiceError as error:
                if error.player_name == "A":
                    self.winner = "B"
                else:
                    self.winner = "A"

                print(
                    f"\nИгрок {error.player_name} нарушил правила: "
                    f"{error.reason}"
                )

                print(
                    f"Игрок {error.player_name} получает "
                    "техническое поражение"
                )

            print(f"\nПобедитель: игрок {self.winner}")
            return self.winner

        finally:
            if self.session_a is not None:
                try:
                    self.player_a.close_game(
                        self.session_a
                    )
                except ServiceClientError:
                    pass

            if self.session_b is not None:
                try:
                    self.player_b.close_game(
                        self.session_b
                    )
                except ServiceClientError:
                    pass

            self.player_a.close()
            self.player_b.close()