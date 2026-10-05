"""Client for Foodisco's Home Assistant endpoints (no Home Assistant imports).

Three calls: swap a pairing code for tokens (ha-pair), read today's totals (ha-status),
report an event (ha-event). Every failure becomes one of four exceptions, so callers
never have to know about HTTP.
"""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import BASE_URL

REQUEST_TIMEOUT = 15


class FoodiscoError(Exception):
    """Base class for everything this client raises."""


class InvalidCode(FoodiscoError):
    """The pairing code is unknown, expired or already used."""


class InvalidAuth(FoodiscoError):
    """The token was revoked or is not valid (re-pair)."""


class RateLimited(FoodiscoError):
    """Asked too soon; try again after `retry_after` seconds."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"rate limited, retry after {retry_after}s")
        self.retry_after = retry_after


class CannotConnect(FoodiscoError):
    """Network failure or a server error."""


class FoodiscoApi:
    """Thin async client."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str = BASE_URL) -> None:
        self._session = session
        self._base = base_url.rstrip("/")

    async def pair(self, code: str) -> dict[str, Any]:
        """Swap a pairing code for {read_token, events_token, account_id, display_name}."""
        return await self._request("POST", "ha-pair", json={"code": code})

    async def status(self, read_token: str) -> dict[str, Any]:
        """Today's totals, the last meal and the planned dinner."""
        return await self._request("GET", "ha-status", token=read_token)

    async def report_event(self, events_token: str, event: str) -> dict[str, Any]:
        """Tell Foodisco that something happened ("oven_finished")."""
        return await self._request("POST", "ha-event", token=events_token, json={"event": event})

    async def _request(
        self,
        method: str,
        function: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.request(
                    method, f"{self._base}/{function}", headers=headers, json=json
                ) as response:
                    status = response.status
                    if status == 200:
                        return await response.json()
                    if status == 429:
                        raise RateLimited(int(response.headers.get("Retry-After", "30")))
                    if status == 401:
                        raise InvalidAuth
                    if status == 400 and function == "ha-pair":
                        raise InvalidCode
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CannotConnect(str(err)) from err
        raise CannotConnect(f"unexpected status {status} from {function}")
