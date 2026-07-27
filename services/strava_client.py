from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()


class StravaClient:
    BASE_URL = "https://www.strava.com/api/v3"
    TOKEN_URL = "https://www.strava.com/oauth/token"

    TOKEN_FILE = (
        Path(__file__).resolve().parent.parent
        / "strava_tokens.json"
    )

    def __init__(self) -> None:
        self.client_id = os.getenv("STRAVA_CLIENT_ID")
        self.client_secret = os.getenv(
            "STRAVA_CLIENT_SECRET"
        )

        initial_refresh_token = os.getenv(
            "STRAVA_REFRESH_TOKEN"
        )

        if not self.client_id:
            raise RuntimeError(
                "STRAVA_CLIENT_ID is missing from .env"
            )

        if not self.client_secret:
            raise RuntimeError(
                "STRAVA_CLIENT_SECRET is missing from .env"
            )

        if not initial_refresh_token:
            raise RuntimeError(
                "STRAVA_REFRESH_TOKEN is missing from .env"
            )

        self.access_token: str | None = None
        self.refresh_token = initial_refresh_token
        self.expires_at = 0

        self._load_saved_tokens()

    def _load_saved_tokens(self) -> None:
        """Load the latest tokens saved by the application."""

        if not self.TOKEN_FILE.exists():
            return

        try:
            token_data = json.loads(
                self.TOKEN_FILE.read_text(
                    encoding="utf-8"
                )
            )

            saved_access_token = token_data.get(
                "access_token"
            )

            saved_refresh_token = token_data.get(
                "refresh_token"
            )

            saved_expires_at = token_data.get(
                "expires_at",
                0,
            )

            if saved_access_token:
                self.access_token = saved_access_token

            if saved_refresh_token:
                self.refresh_token = saved_refresh_token

            self.expires_at = int(saved_expires_at)

        except (
            json.JSONDecodeError,
            OSError,
            TypeError,
            ValueError,
        ):
            # If the file is damaged, the app can still
            # recover using the refresh token from .env.
            self.access_token = None
            self.expires_at = 0

    def _save_tokens(self) -> None:
        """Persist the latest Strava tokens safely."""

        token_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }

        temporary_file = self.TOKEN_FILE.with_suffix(
            ".tmp"
        )

        temporary_file.write_text(
            json.dumps(token_data, indent=2),
            encoding="utf-8",
        )

        temporary_file.replace(self.TOKEN_FILE)

    def _refresh_access_token(self) -> None:
        """Request and store a fresh access token."""

        response = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=15,
        )

        response.raise_for_status()

        token_data = response.json()

        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.expires_at = int(token_data["expires_at"])

        self._save_tokens()

    def _ensure_access_token(self) -> None:
        """Refresh shortly before the token expires."""

        refresh_buffer_seconds = 120

        token_is_missing = not self.access_token

        token_is_expired = (
            time.time()
            >= self.expires_at - refresh_buffer_seconds
        )

        if token_is_missing or token_is_expired:
            self._refresh_access_token()

    def _headers(self) -> dict[str, str]:
        self._ensure_access_token()

        return {
            "Authorization": f"Bearer {self.access_token}"
        }

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Make a Strava GET request and retry once on 401."""

        response = requests.get(
            f"{self.BASE_URL}{endpoint}",
            headers=self._headers(),
            params=params,
            timeout=15,
        )

        if response.status_code == 401:
            self.access_token = None
            self.expires_at = 0

            self._refresh_access_token()

            response = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self._headers(),
                params=params,
                timeout=15,
            )

        response.raise_for_status()
        return response

    def get_athlete(self) -> dict:
        response = self._get("/athlete")
        return response.json()

    def get_activities(
        self,
        after: int | None = None,
        before: int | None = None,
        per_page: int = 50,
    ) -> list[dict]:
        params: dict[str, int] = {
            "page": 1,
            "per_page": per_page,
        }

        if after is not None:
            params["after"] = after

        if before is not None:
            params["before"] = before

        response = self._get(
            "/athlete/activities",
            params=params,
        )

        return response.json()