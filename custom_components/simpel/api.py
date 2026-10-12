"""Client for the web API behind the Mijn Simpel customer portal."""

from __future__ import annotations

from typing import Any

import aiohttp

API_URL = "https://api.simpel.nl"
PORTAL_API_URL = "https://mijn.simpel.nl/api"
TIMEOUT = aiohttp.ClientTimeout(total=30)

# Endpoints read on every refresh, keyed by the name the sensors use.
USAGE_PATHS = {
    "summary": "usage/usage-summary",
    "cdrs": "usage/cdrs",
    "dashboard": "dashboard",
    "products": "subscription/products",
}


class SimpelError(Exception):
    """Simpel could not be reached or answered unexpectedly."""


class SimpelAuthError(SimpelError):
    """Simpel rejected the username or password."""


class SimpelClient:
    """Logs in to Simpel and reads usage, logging in again when the session expires."""

    def __init__(self, session: aiohttp.ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password

    async def login(self) -> None:
        """Start a session; Simpel answers with session cookies on .simpel.nl."""
        payload = {"username": self._username, "password": self._password, "remember": True}
        async with self._session.post(f"{API_URL}/login", json=payload, timeout=TIMEOUT) as resp:
            if resp.status == 400:
                raise SimpelAuthError("Simpel rejected the login")
            if resp.status == 429:
                raise SimpelError("Simpel is rate limiting logins")
            if resp.status != 200:
                raise SimpelError(f"Login failed with HTTP {resp.status}")

    async def subscription_id(self) -> str:
        """Return the id of the main subscription on the account."""
        overview = await self._get(f"{API_URL}/account/subscription-overview")
        return overview["mainSubscription"]["subscriptionId"]

    async def usage(self, subscription_id: str) -> dict[str, Any]:
        """Return the raw usage payloads for one subscription."""
        return {
            name: await self._get(f"{PORTAL_API_URL}/{path}", {"sid": subscription_id})
            for name, path in USAGE_PATHS.items()
        }

    async def _get(self, url: str, params: dict[str, str] | None = None) -> Any:
        for attempt in range(2):
            async with self._session.get(url, params=params, timeout=TIMEOUT) as resp:
                if resp.status in (401, 403) and attempt == 0:
                    await self.login()
                    continue
                if resp.status != 200:
                    raise SimpelError(f"GET {url} failed with HTTP {resp.status}")
                return await resp.json(content_type=None)
        raise SimpelError(f"GET {url} still unauthorised after logging in")
