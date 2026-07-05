"""Sensor platform: number of available connectors at a station."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CONNECTOR_TYPES,
    ATTR_OWNER,
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
    """Set up the availability sensor for a station."""
    coordinator: InChargeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([InChargeAvailabilitySensor(coordinator, entry)])


class InChargeAvailabilitySensor(
    CoordinatorEntity[InChargeCoordinator], SensorEntity
):
    """Number of connectors currently free at a charging station."""

    _attr_has_entity_name = True
    _attr_name = "Available connectors"
    _attr_icon = "mdi:ev-station"
    _attr_native_unit_of_measurement = "connectors"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, coordinator: InChargeCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        station_id = entry.data[CONF_STATION_ID]
        self._attr_unique_id = f"{station_id}_available_connectors"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=entry.title,
            manufacturer="Vattenfall InCharge (unofficial)",
            model=station_id,
        )

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data
        return data.get("available") if data else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data or {}
        return {
            ATTR_TOTAL: data.get("total"),
            ATTR_STREET: data.get("street"),
            ATTR_OWNER: data.get("owner"),
            ATTR_STATION_ID: data.get("id"),
            ATTR_CONNECTOR_TYPES: data.get("connector_types"),
        }
