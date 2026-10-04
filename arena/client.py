import httpx


class ServiceClientError(Exception):
    """Ошибка при взаимодействии с игровым сервисом."""


class ServiceTimeoutError(ServiceClientError):
    """Сервис не ответил за допустимое время."""


class ServiceClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

    def _request_json(
        self,
        method: str,
        path: str,
        **kwargs,
    ):
        try:
            response = self.client.request(
                method,
                path,
                **kwargs,
            )

        except httpx.TimeoutException:
            raise ServiceTimeoutError(
                f"сервис не ответил за {self.timeout} секунду"
            ) from None

        except httpx.RequestError as error:
            raise ServiceClientError(
                f"ошибка соединения с сервисом: {error}"
            ) from None

        if not response.is_success:
            raise ServiceClientError(
                f"сервис вернул HTTP {response.status_code}"
            )

        try:
            return response.json()

        except ValueError:
            raise ServiceClientError(
                "сервис вернул некорректный JSON"
            ) from None

    def create_game(self):
        data = self._request_json(
            "POST",
            "/game",
        )

        if not isinstance(data, dict):
            raise ServiceClientError(
                "некорректный ответ POST /game"
            )

        if "session_id" not in data:
            raise ServiceClientError(
                "в ответе POST /game отсутствует session_id"
            )

        if "ships" not in data:
            raise ServiceClientError(
                "в ответе POST /game отсутствует ships"
            )

        return data

    def make_shot(self, session_id: str):
        data = self._request_json(
            "POST",
            f"/game/{session_id}/shot",
        )

        coordinate = data.get("coordinate")

        if not isinstance(coordinate, str):
            raise ServiceClientError(
                "сервис вернул некорректную координату"
            )

        return coordinate

    def opponent_shot(
        self,
        session_id: str,
        coordinate: str,
    ):
        data = self._request_json(
            "POST",
            f"/game/{session_id}/opponent-shot",
            json={"coordinate": coordinate},
        )

        result = data.get("result")

        if result not in ("miss", "hit", "killed"):
            raise ServiceClientError(
                "сервис вернул некорректный результат выстрела"
            )

        return result

    def send_shot_result(
        self,
        session_id: str,
        result: str,
    ):
        data = self._request_json(
            "POST",
            f"/game/{session_id}/shot/result",
            json={"result": result},
        )

        if data.get("status") != "accepted":
            raise ServiceClientError(
                "сервис не подтвердил результат выстрела"
            )

        return data

    def close_game(self, session_id: str):
        data = self._request_json(
            "POST",
            f"/game/{session_id}/close",
        )

        if data.get("status") != "closed":
            raise ServiceClientError(
                "сервис не подтвердил закрытие сессии"
            )

        return data

    def close(self):
        self.client.close()