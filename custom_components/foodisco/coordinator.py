"""Polls Foodisco once a minute and notices a newly logged meal."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, FoodiscoApi, InvalidAuth, RateLimited
from .const import CONF_READ_TOKEN, DOMAIN, SCAN_INTERVAL
from .logic import detect_new_meal

_LOGGER = logging.getLogger(__name__)

FoodiscoConfigEntry = ConfigEntry["FoodiscoCoordinator"]


class FoodiscoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """One coordinator per paired person."""

    config_entry: FoodiscoConfigEntry

    def __init__(self, hass: HomeAssistant, entry: FoodiscoConfigEntry, api: FoodiscoApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = api
        # Set on the refresh that saw a new meal, None otherwise; the event entity reads it.
        self.new_meal: str | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.status(self.config_entry.data[CONF_READ_TOKEN])
        except InvalidAuth as err:
            # The token was revoked (in the app) — ask for a new pairing code.
            raise ConfigEntryAuthFailed from err
        except RateLimited as err:
            raise UpdateFailed(f"Foodisco asked us to slow down ({err.retry_after}s)") from err
        except CannotConnect as err:
            raise UpdateFailed(f"Cannot reach Foodisco: {err}") from err

        # self.data is None on the first refresh, so setup and restarts never look like a meal.
        self.new_meal = detect_new_meal(self.data, data)
        return data
