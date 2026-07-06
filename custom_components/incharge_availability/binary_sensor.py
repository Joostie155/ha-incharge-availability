"""Binary sensor: is at least one connector free at a station."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_OCCUPIED,
    ATTR_STATION_ID,
    ATTR_STREET,
    ATTR_TOTAL,
    DOMAIN,
)
from .coordinator import InChargeHub, InChargeRegionCoordinator
from .entity import InChargeStationEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the availability binary sensor for a station."""
    hub: InChargeHub = hass.data[DOMAIN]
    coordinator, station_id = hub.runtime[entry.entry_id]
    async_add_entities(
        [InChargeAvailableBinarySensor(coordinator, station_id, entry.title)]
    )


class InChargeAvailableBinarySensor(InChargeStationEntity, BinarySensorEntity):
    """On when at least one connector is free, off when the station is full."""

    _attr_name = "Available"
    _attr_icon = "mdi:ev-station"

    def __init__(
        self,
        coordinator: InChargeRegionCoordinator,
        station_id: str,
        station_name: str,
    ) -> None:
        super().__init__(coordinator, station_id, station_name)
        self._attr_unique_id = f"{station_id}_available"

    @property
    def is_on(self) -> bool | None:
        station = self._station
        if not station:
            return None
        return (station.get("available") or 0) > 0

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        station = self._station or {}
        return {
            "available": station.get("available"),
            ATTR_OCCUPIED: station.get("occupied"),
            ATTR_TOTAL: station.get("total"),
            ATTR_STREET: station.get("street"),
            ATTR_STATION_ID: station.get("id"),
        }
