"""Binary sensor: is at least one connector free at a station."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_STATION_ID,
    ATTR_STREET,
    ATTR_TOTAL,
    CONF_STATION_ID,
    DOMAIN,
)
from .coordinator import InChargeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the availability binary sensor for a station."""
    coordinator: InChargeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([InChargeAvailableBinarySensor(coordinator, entry)])


class InChargeAvailableBinarySensor(
    CoordinatorEntity[InChargeCoordinator], BinarySensorEntity
):
    """On when at least one connector is free, off when the station is full."""

    _attr_has_entity_name = True
    _attr_name = "Available"
    _attr_icon = "mdi:ev-station"

    def __init__(
        self, coordinator: InChargeCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        station_id = entry.data[CONF_STATION_ID]
        self._attr_unique_id = f"{station_id}_available"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=entry.title,
            manufacturer="Vattenfall InCharge (unofficial)",
            model=station_id,
        )

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if not data:
            return None
        return (data.get("available") or 0) > 0

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data or {}
        return {
            "available": data.get("available"),
            ATTR_TOTAL: data.get("total"),
            ATTR_STREET: data.get("street"),
            ATTR_STATION_ID: data.get("id"),
        }
