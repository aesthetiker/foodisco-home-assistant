"""A "meal logged" event — the trigger to hang automations on."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ACCOUNT_ID, MEAL_TYPES
from .coordinator import FoodiscoConfigEntry, FoodiscoCoordinator
from .sensor import device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: FoodiscoConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([FoodiscoMealEvent(entry)])


class FoodiscoMealEvent(CoordinatorEntity[FoodiscoCoordinator], EventEntity):
    """Fires once per newly logged meal, with the meal type as event_type.

    Unlike a sensor's state change this never fires on a restart or a reconnect:
    the coordinator only reports a meal logged after the last one it saw.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "meal_logged"
    _attr_event_types = MEAL_TYPES

    def __init__(self, entry: FoodiscoConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        self._attr_unique_id = f"{entry.data[CONF_ACCOUNT_ID]}_meal_logged"
        self._attr_device_info = device_info(entry)

    @callback
    def _handle_coordinator_update(self) -> None:
        meal = self.coordinator.new_meal
        if meal:
            self._trigger_event(meal)
        self.async_write_ha_state()
