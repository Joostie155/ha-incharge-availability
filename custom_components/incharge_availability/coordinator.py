"""DataUpdateCoordinator that polls one station's live availability."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import InChargeApi, InChargeApiError, parse_station
from .const import DEFAULT_SCAN_INTERVAL_MINUTES, DEG_PER_KM, DOMAIN

_LOGGER = logging.getLogger(__name__)


class InChargeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches and caches the live availability of a single station."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: InChargeApi,
        station_id: str,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {station_id}",
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        self._api = api
        self._station_id = station_id
        self._latitude = latitude
        self._longitude = longitude
        self._radius_km = radius_km

    async def _async_update_data(self) -> dict[str, Any]:
        margin = max(self._radius_km, 0.1) * DEG_PER_KM
        try:
            raw = await self._api.async_station_by_id(
                self._station_id, self._latitude, self._longitude, margin
            )
        except InChargeApiError as err:
            raise UpdateFailed(f"InCharge API error: {err}") from err
        if raw is None:
            raise UpdateFailed(f"Station {self._station_id} not found nearby")
        return parse_station(raw)
