"""Setup dialog: type the pairing code from the Foodisco app."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, FoodiscoApi, InvalidCode
from .const import (
    CONF_ACCOUNT_ID,
    CONF_DISPLAY_NAME,
    CONF_EVENTS_TOKEN,
    CONF_READ_TOKEN,
    DOMAIN,
)

CODE_SCHEMA = vol.Schema({vol.Required("code"): str})


class FoodiscoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pair one Foodisco account (one person) with this Home Assistant."""

    VERSION = 1

    async def _pair(self, code: str) -> tuple[dict[str, Any] | None, str | None]:
        """Exchange the code; return (data, error_key)."""
        api = FoodiscoApi(async_get_clientsession(self.hass))
        try:
            paired = await api.pair(code)
        except InvalidCode:
            return None, "invalid_code"
        except CannotConnect:
            return None, "cannot_connect"
        except Exception:  # noqa: BLE001 - the dialog must never crash on a surprise
            return None, "unknown"
        return {
            CONF_READ_TOKEN: paired["read_token"],
            CONF_EVENTS_TOKEN: paired["events_token"],
            CONF_ACCOUNT_ID: paired["account_id"],
            CONF_DISPLAY_NAME: paired.get("display_name"),
        }, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data, error = await self._pair(user_input["code"])
            if data:
                await self.async_set_unique_id(data[CONF_ACCOUNT_ID])
                # Pairing again replaces the old tokens on Foodisco's side, so an
                # existing entry for this person must take the new ones.
                self._abort_if_unique_id_configured(updates=data)
                name = data[CONF_DISPLAY_NAME]
                return self.async_create_entry(title=f"Foodisco {name}" if name else "Foodisco", data=data)
            errors["base"] = error or "unknown"
        return self.async_show_form(step_id="user", data_schema=CODE_SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data, error = await self._pair(user_input["code"])
            if data:
                await self.async_set_unique_id(data[CONF_ACCOUNT_ID])
                # A code from another person must not silently swap the account.
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates=data)
            errors["base"] = error or "unknown"
        return self.async_show_form(step_id="reauth_confirm", data_schema=CODE_SCHEMA, errors=errors)
