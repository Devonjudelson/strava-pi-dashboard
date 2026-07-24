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

    def get_athlete(self) -> dict:
        response = requests.get(
            f"{self.BASE_URL}/athlete",
            headers={
                "Authorization": f"Bearer {self.access_token}"
            },
            timeout=15,
        )

        response.raise_for_status()
        return response.json()