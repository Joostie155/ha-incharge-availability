"""Sensor platform: available / occupied connectors, plus per-type breakdown."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CITY,
    ATTR_CONNECTOR_TYPES,
    ATTR_MAX_POWER_KW,
    ATTR_OCCUPIED,
    ATTR_OWNER,
    ATTR_STATION_ID,
    ATTR_STREET,
    ATTR_TOTAL,
    DOMAIN,
)
from .coordinator import InChargeHub, InChargeRegionCoordinator
from .entity import InChargeStationEntity

_UNIT_CONNECTORS = "connectors"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the availability sensors for a station."""
    hub: InChargeHub = hass.data[DOMAIN]
    coordinator, station_id = hub.runtime[entry.entry_id]
    name = entry.title

    entities: list[SensorEntity] = [
        InChargeAvailabilitySensor(coordinator, station_id, name),
        InChargeOccupiedSensor(coordinator, station_id, name),
    ]

    # One "<type> available" sensor per connector type present at setup. New
    # types that appear later are picked up on the next reload of the entry.
    station = (coordinator.data or {}).get(station_id) or {}
    for group in station.get("connector_types", []):
        connector_type = group.get("type")
        if connector_type:
            entities.append(
                InChargeConnectorTypeSensor(
                    coordinator, station_id, name, connector_type
                )
            )

    async_add_entities(entities)


class InChargeAvailabilitySensor(InChargeStationEntity, SensorEntity):
    """Number of connectors currently free at a charging station."""

    _attr_name = "Available connectors"
    _attr_icon = "mdi:ev-station"
    _attr_native_unit_of_measurement = _UNIT_CONNECTORS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: InChargeRegionCoordinator,
        station_id: str,
        station_name: str,
    ) -> None:
        super().__init__(coordinator, station_id, station_name)
        self._attr_unique_id = f"{station_id}_available_connectors"

    @property
    def native_value(self) -> int | None:
        station = self._station
        return station.get("available") if station else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        station = self._station or {}
        return {
            ATTR_TOTAL: station.get("total"),
            ATTR_OCCUPIED: station.get("occupied"),
            ATTR_STREET: station.get("street"),
            ATTR_CITY: station.get("city"),
            ATTR_OWNER: station.get("owner"),
            ATTR_MAX_POWER_KW: station.get("max_power_kw"),
            ATTR_STATION_ID: station.get("id"),
            ATTR_CONNECTOR_TYPES: station.get("connector_types"),
        }


class InChargeOccupiedSensor(InChargeStationEntity, SensorEntity):
    """Connectors that are not free — charging or out of service."""

    _attr_name = "Occupied connectors"
    _attr_icon = "mdi:ev-plug-type2"
    _attr_native_unit_of_measurement = _UNIT_CONNECTORS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: InChargeRegionCoordinator,
        station_id: str,
        station_name: str,
    ) -> None:
        super().__init__(coordinator, station_id, station_name)
        self._attr_unique_id = f"{station_id}_occupied_connectors"

    @property
    def native_value(self) -> int | None:
        station = self._station
        return station.get("occupied") if station else None


class InChargeConnectorTypeSensor(InChargeStationEntity, SensorEntity):
    """Number of free connectors of one specific type (e.g. Type2, CCS)."""

    _attr_icon = "mdi:ev-plug-type2"
    _attr_native_unit_of_measurement = _UNIT_CONNECTORS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: InChargeRegionCoordinator,
        station_id: str,
        station_name: str,
        connector_type: str,
    ) -> None:
        super().__init__(coordinator, station_id, station_name)
        self._connector_type = connector_type
        self._attr_name = f"{connector_type} available"
        self._attr_unique_id = f"{station_id}_available_{connector_type}"

    def _group(self) -> dict[str, object] | None:
        station = self._station
        if not station:
            return None
        for group in station.get("connector_types", []):
            if group.get("type") == self._connector_type:
                return group
        return None

    @property
    def native_value(self) -> int | None:
        group = self._group()
        return group.get("available") if group else None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        group = self._group() or {}
        return {ATTR_TOTAL: group.get("count")}
