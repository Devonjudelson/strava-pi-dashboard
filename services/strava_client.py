from __future__ import annotations
import os

import requests
from dotenv import load_dotenv


load_dotenv()


class StravaClient:
    BASE_URL = "https://www.strava.com/api/v3"

    def __init__(self) -> None:
        self.access_token = os.getenv("STRAVA_ACCESS_TOKEN")

        if not self.access_token:
            raise ValueError(
                "STRAVA_ACCESS_TOKEN was not found in the .env file."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}"
        }

    def get_athlete(self) -> dict:
        response = requests.get(
            f"{self.BASE_URL}/athlete",
            headers=self._headers(),
            timeout=15,
        )

        response.raise_for_status()
        return response.json()

    def get_activities(
        self,
        after: int | None = None,
        before: int | None = None,
        per_page: int = 50,
    ) -> list[dict]:
        params = {
            "page": 1,
            "per_page": per_page,
        }

        if after is not None:
            params["after"] = after

        if before is not None:
            params["before"] = before

        response = requests.get(
            f"{self.BASE_URL}/athlete/activities",
            headers=self._headers(),
            params=params,
            timeout=15,
        )

        response.raise_for_status()
        return response.json()