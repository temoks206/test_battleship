import httpx


class ServiceClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

    def create_game(self):
        """Создаёт новую игровую сессию."""

        response = self.client.post("/game")
        response.raise_for_status()

        return response.json()

    def make_shot(self, session_id: str):
        """Запрашивает следующий выстрел сервиса."""

        response = self.client.post(
            f"/game/{session_id}/shot"
        )

        response.raise_for_status()

        return response.json()["coordinate"]

    def opponent_shot(
        self,
        session_id: str,
        coordinate: str,
    ):
        """Передаёт сервису выстрел противника."""

        response = self.client.post(
            f"/game/{session_id}/opponent-shot",
            json={
                "coordinate": coordinate,
            },
        )

        response.raise_for_status()

        return response.json()["result"]

    def send_shot_result(
        self,
        session_id: str,
        result: str,
    ):
        """Передаёт сервису результат его выстрела."""

        response = self.client.post(
            f"/game/{session_id}/shot/result",
            json={
                "result": result,
            },
        )

        response.raise_for_status()

        return response.json()

    def close_game(self, session_id: str):
        """Закрывает игровую сессию."""

        response = self.client.post(
            f"/game/{session_id}/close"
        )

        response.raise_for_status()

        return response.json()

    def close(self):
        """Закрывает HTTP-клиент."""

        self.client.close()