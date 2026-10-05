"""Foodisco: today's nutrition totals and meal events in Home Assistant."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import CannotConnect, FoodiscoApi, FoodiscoError, InvalidAuth, RateLimited
from .const import CONF_EVENTS_TOKEN, DOMAIN, REPORTABLE_EVENTS
from .coordinator import FoodiscoConfigEntry, FoodiscoCoordinator

PLATFORMS = [Platform.SENSOR, Platform.EVENT]

SERVICE_REPORT_EVENT = "report_event"
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("event"): vol.In(REPORTABLE_EVENTS),
        vol.Optional("config_entry_id"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the report_event service once for the whole domain."""

    async def report_event(call: ServiceCall) -> None:
        entries = [
            e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED
        ]
        wanted = call.data.get("config_entry_id")
        if wanted:
            entries = [e for e in entries if e.entry_id == wanted]
        if not entries:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_account")
        if len(entries) > 1:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="choose_account")

        entry: FoodiscoConfigEntry = entries[0]
        try:
            await entry.runtime_data.api.report_event(entry.data[CONF_EVENTS_TOKEN], call.data["event"])
        except InvalidAuth as err:
            entry.async_start_reauth(hass)
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="reauth_needed") from err
        except RateLimited as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="rate_limited") from err
        except (CannotConnect, FoodiscoError) as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="cannot_connect") from err

    hass.services.async_register(DOMAIN, SERVICE_REPORT_EVENT, report_event, schema=SERVICE_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FoodiscoConfigEntry) -> bool:
    coordinator = FoodiscoCoordinator(hass, entry, FoodiscoApi(async_get_clientsession(hass)))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FoodiscoConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
