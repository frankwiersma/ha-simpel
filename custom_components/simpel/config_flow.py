"""Ask for the Mijn Simpel login once; a password change is picked up through reauth."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import SimpelAuthError, SimpelClient, SimpelError
from .const import CONF_SUBSCRIPTION_ID, DOMAIN

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
    }
)
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR})


async def _validate(username: str, password: str) -> str:
    """Log in and return the subscription id."""
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
        client = SimpelClient(session, username, password)
        await client.login()
        return await client.subscription_id()


def _error(err: Exception) -> str:
    return "invalid_auth" if isinstance(err, SimpelAuthError) else "cannot_connect"


class SimpelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Simpel."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for username and password."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                subscription_id = await _validate(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            except (SimpelError, aiohttp.ClientError, TimeoutError) as err:
                errors["base"] = _error(err)
            else:
                await self.async_set_unique_id(subscription_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Simpel",
                    data={**user_input, CONF_SUBSCRIPTION_ID: subscription_id},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Simpel rejected the stored password."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the new password."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate(entry.data[CONF_USERNAME], user_input[CONF_PASSWORD])
            except (SimpelError, aiohttp.ClientError, TimeoutError) as err:
                errors["base"] = _error(err)
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=errors,
        )
