"""Shared base for entities backed by a shared region coordinator."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InChargeRegionCoordinator


class InChargeStationEntity(CoordinatorEntity[InChargeRegionCoordinator]):
    """An entity for one station within a shared, multi-station coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: InChargeRegionCoordinator,
        station_id: str,
        station_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=station_name,
            manufacturer="Vattenfall InCharge (unofficial)",
            model=station_id,
        )

    @property
    def _station(self) -> dict[str, Any] | None:
        """This entity's station within the coordinator's region payload."""
        return (self.coordinator.data or {}).get(self._station_id)

    @property
    def available(self) -> bool:
        """Unavailable if the poll failed or the station left the search box."""
        return super().available and self._station is not None
