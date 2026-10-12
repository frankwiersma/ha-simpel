"""Polls Simpel for the current bundle usage."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SimpelAuthError, SimpelClient, SimpelError
from .const import CONF_SUBSCRIPTION_ID, DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

type SimpelConfigEntry = ConfigEntry[SimpelCoordinator]


class SimpelCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Holds the Simpel session and refreshes the usage payloads."""

    config_entry: SimpelConfigEntry

    def __init__(self, hass: HomeAssistant, entry: SimpelConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        # A dedicated session keeps Simpel's cookies apart from the shared one.
        self.session = async_create_clientsession(
            hass, auto_cleanup=False, cookie_jar=aiohttp.CookieJar()
        )
        self.client = SimpelClient(
            self.session, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
        )
        self.subscription_id: str = entry.data[CONF_SUBSCRIPTION_ID]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.usage(self.subscription_id)
        except SimpelAuthError as err:
            raise ConfigEntryAuthFailed(err) from err
        except (SimpelError, aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(err) from err
