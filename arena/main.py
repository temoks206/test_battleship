import argparse

from arena.match import Match


def main():
    parser = argparse.ArgumentParser(
        description="Арена для игры между двумя Battleship-сервисами"
    )

    parser.add_argument(
        "service_a",
        help="Адрес первого сервиса",
    )

    parser.add_argument(
        "service_b",
        help="Адрес второго сервиса",
    )

    args = parser.parse_args()

    print("Начинаем матч")
    print(f"Игрок A: {args.service_a}")
    print(f"Игрок B: {args.service_b}")
    print()

    match = Match(
        service_a_url=args.service_a,
        service_b_url=args.service_b,
    )

    winner = match.play()

    print(
        f"\nМатч завершён. Победитель: игрок {winner}"
    )


if __name__ == "__main__":
    main()