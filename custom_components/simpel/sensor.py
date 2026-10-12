"""Sensors for the remaining Simpel bundle."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import SimpelConfigEntry, SimpelCoordinator


def _remaining(data: dict[str, Any], bundle: str) -> int | None:
    return data["summary"][bundle]["amount"]


def _used(data: dict[str, Any], bundle: str) -> int | None:
    item = data["summary"][bundle]
    if item["totalAmount"] is None or item["amount"] is None:
        return None
    return item["totalAmount"] - item["amount"]


def _period_day(data: dict[str, Any], edge: str) -> date:
    """Billing cycle edges are midnights; the end one is the cycle's last day."""
    return datetime.fromisoformat(data["dashboard"]["billingCycle"][edge]).date()


def _days_left(data: dict[str, Any]) -> int:
    """Days left in the billing cycle, today included."""
    return max((_period_day(data, "end") - dt_util.now().date()).days + 1, 1)


def _data_per_day_left(data: dict[str, Any]) -> int | None:
    remaining = _remaining(data, "data")
    if remaining is None:
        return None
    return round(remaining / _days_left(data))


@dataclass(frozen=True, kw_only=True)
class SimpelSensorDescription(SensorEntityDescription):
    """A sensor with the function that reads its value."""

    value_fn: Callable[[dict[str, Any]], Any]


DATA_SIZE = {
    "native_unit_of_measurement": UnitOfInformation.MEGABYTES,
    "suggested_unit_of_measurement": UnitOfInformation.GIGABYTES,
    "suggested_display_precision": 1,
    "device_class": SensorDeviceClass.DATA_SIZE,
}

SENSORS = (
    SimpelSensorDescription(
        key="data_remaining",
        translation_key="data_remaining",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _remaining(d, "data"),
        **DATA_SIZE,
    ),
    SimpelSensorDescription(
        key="data_used",
        translation_key="data_used",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _used(d, "data"),
        **DATA_SIZE,
    ),
    SimpelSensorDescription(
        key="data_bundle",
        translation_key="data_bundle",
        value_fn=lambda d: d["summary"]["data"]["totalAmount"],
        **DATA_SIZE,
    ),
    SimpelSensorDescription(
        key="data_per_day_left",
        translation_key="data_per_day_left",
        value_fn=_data_per_day_left,
    ),
    SimpelSensorDescription(
        key="days_left",
        translation_key="days_left",
        native_unit_of_measurement=UnitOfTime.DAYS,
        value_fn=_days_left,
    ),
    SimpelSensorDescription(
        key="voice_remaining",
        translation_key="voice_remaining",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _remaining(d, "voice"),
    ),
    SimpelSensorDescription(
        key="voice_used",
        translation_key="voice_used",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _used(d, "voice"),
    ),
    SimpelSensorDescription(
        key="sms_remaining",
        translation_key="sms_remaining",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _remaining(d, "sms"),
    ),
    SimpelSensorDescription(
        key="period_start",
        translation_key="period_start",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: _period_day(d, "start"),
    ),
    SimpelSensorDescription(
        key="period_end",
        translation_key="period_end",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: _period_day(d, "end"),
    ),
    SimpelSensorDescription(
        key="data_updated",
        translation_key="data_updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: datetime.fromisoformat(d["cdrs"]["lastUpdateData"]),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimpelConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one sensor per description."""
    async_add_entities(SimpelSensor(entry.runtime_data, d) for d in SENSORS)


class SimpelSensor(CoordinatorEntity[SimpelCoordinator], SensorEntity):
    """One value from the Simpel usage payloads."""

    _attr_has_entity_name = True
    entity_description: SimpelSensorDescription

    def __init__(
        self, coordinator: SimpelCoordinator, description: SimpelSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.subscription_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.subscription_id)},
            name="Simpel",
            manufacturer="Simpel",
            model=coordinator.data["products"]["data"]["title"],
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://mijn.simpel.nl",
        )

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)
