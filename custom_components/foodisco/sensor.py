"""Sensors: what is left for today, and the last and planned meals."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ACCOUNT_ID, CONF_DISPLAY_NAME, DOMAIN
from .coordinator import FoodiscoConfigEntry, FoodiscoCoordinator
from .logic import last_meal


@dataclass(frozen=True, kw_only=True)
class FoodiscoSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


def _planned_dinner(data: dict[str, Any]) -> str | None:
    return data.get("planned_dinner")


def _last_meal_time(data: dict[str, Any]) -> datetime | None:
    return last_meal(data)[1]


SENSORS: tuple[FoodiscoSensorDescription, ...] = (
    FoodiscoSensorDescription(
        key="kcal_remaining",
        translation_key="kcal_remaining",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("kcal_remaining"),
    ),
    FoodiscoSensorDescription(
        key="kcal_today",
        translation_key="kcal_today",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("kcal_today"),
    ),
    FoodiscoSensorDescription(
        key="protein_today",
        translation_key="protein_today",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("protein_today_g"),
    ),
    FoodiscoSensorDescription(
        key="water_today",
        translation_key="water_today",
        native_unit_of_measurement="mL",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("water_ml"),
    ),
    FoodiscoSensorDescription(
        key="last_meal",
        translation_key="last_meal",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_last_meal_time,
    ),
    FoodiscoSensorDescription(
        key="planned_dinner",
        translation_key="planned_dinner",
        value_fn=_planned_dinner,
    ),
)


def device_info(entry: FoodiscoConfigEntry) -> DeviceInfo:
    """One device per paired person."""
    name = entry.data.get(CONF_DISPLAY_NAME)
    return DeviceInfo(
        identifiers={(DOMAIN, entry.data[CONF_ACCOUNT_ID])},
        name=f"Foodisco {name}" if name else "Foodisco",
        manufacturer="Foodisco",
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: FoodiscoConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(FoodiscoSensor(entry, d) for d in SENSORS)


class FoodiscoSensor(CoordinatorEntity[FoodiscoCoordinator], SensorEntity):
    _attr_has_entity_name = True
    entity_description: FoodiscoSensorDescription

    def __init__(self, entry: FoodiscoConfigEntry, description: FoodiscoSensorDescription) -> None:
        super().__init__(entry.runtime_data)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data[CONF_ACCOUNT_ID]}_{description.key}"
        self._attr_device_info = device_info(entry)

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "last_meal":
            meal_type, _ = last_meal(self.coordinator.data)
            return {"meal_type": meal_type} if meal_type else None
        return None
