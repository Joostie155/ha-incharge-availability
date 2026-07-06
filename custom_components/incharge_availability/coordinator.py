"""Coordinator + hub that poll InCharge availability, batched per search area.

Every station a user adds carries the ``(latitude, longitude, radius)`` search
box it was found in. The InCharge ``/Stations`` endpoint already returns *every*
station inside such a box in a single request, so stations that share a box also
share one :class:`InChargeRegionCoordinator` and one poll — adding five poles in
the same street costs one request per interval, not five.

:class:`InChargeHub` owns that de-duplication: it keys coordinators by a rounded
search box, ref-counts the config entries pointing at each one, and tears a
coordinator down when its last entry unloads.
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import InChargeApi, InChargeApiError, parse_station
from .const import DEG_PER_KM, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Coordinators are shared between entries whose search box matches once rounded
# to this precision. ~1e-4 deg is ~11 m — fine enough that two stations picked
# from the same map view collapse onto one poll.
_COORD_PRECISION = 4
_RADIUS_PRECISION = 3

type RegionKey = tuple[float, float, float]


class InChargeRegionCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls one search box; exposes every station in it, keyed by station id."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: InChargeApi,
        latitude: float,
        longitude: float,
        radius_km: float,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {latitude:.4f},{longitude:.4f}",
            update_interval=update_interval,
        )
        self._api = api
        self._latitude = latitude
        self._longitude = longitude
        self._radius_km = radius_km

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        margin = max(self._radius_km, 0.1) * DEG_PER_KM
        try:
            stations = await self._api.async_stations_near(
                self._latitude, self._longitude, margin
            )
        except InChargeApiError as err:
            raise UpdateFailed(f"InCharge API error: {err}") from err
        return {s["id"]: parse_station(s) for s in stations}


class InChargeHub:
    """Owns the shared coordinators and maps config entries onto them."""

    def __init__(self, hass: HomeAssistant, api: InChargeApi) -> None:
        self._hass = hass
        self._api = api
        self._coordinators: dict[RegionKey, InChargeRegionCoordinator] = {}
        # key -> {entry_id: poll interval in minutes}, used to ref-count and to
        # pick the tightest interval any sharer asked for.
        self._members: dict[RegionKey, dict[str, int]] = {}
        # entry_id -> (coordinator, station_id) for the platforms to look up.
        self.runtime: dict[str, tuple[InChargeRegionCoordinator, str]] = {}

    @staticmethod
    def _key(latitude: float, longitude: float, radius_km: float) -> RegionKey:
        return (
            round(latitude, _COORD_PRECISION),
            round(longitude, _COORD_PRECISION),
            round(radius_km, _RADIUS_PRECISION),
        )

    @property
    def is_empty(self) -> bool:
        """True when no config entry is using this hub any more."""
        return not self.runtime

    async def async_setup_entry(
        self,
        entry_id: str,
        station_id: str,
        latitude: float,
        longitude: float,
        radius_km: float,
        interval_minutes: int,
    ) -> InChargeRegionCoordinator:
        """Attach an entry to its (possibly shared) coordinator."""
        key = self._key(latitude, longitude, radius_km)
        members = self._members.setdefault(key, {})
        members[entry_id] = interval_minutes
        new_interval = timedelta(minutes=min(members.values()))

        coordinator = self._coordinators.get(key)
        if coordinator is None:
            coordinator = InChargeRegionCoordinator(
                self._hass, self._api, latitude, longitude, radius_km, new_interval
            )
            self._coordinators[key] = coordinator
            await coordinator.async_config_entry_first_refresh()
        else:
            # A newcomer may want a tighter interval than the existing sharers.
            coordinator.update_interval = new_interval

        self.runtime[entry_id] = (coordinator, station_id)
        return coordinator

    def async_unload_entry(
        self,
        entry_id: str,
        latitude: float,
        longitude: float,
        radius_km: float,
    ) -> None:
        """Detach an entry; drop the coordinator when its last sharer leaves."""
        self.runtime.pop(entry_id, None)
        key = self._key(latitude, longitude, radius_km)
        members = self._members.get(key)
        if members is None:
            return
        members.pop(entry_id, None)
        if not members:
            self._members.pop(key, None)
            self._coordinators.pop(key, None)
        else:
            self._coordinators[key].update_interval = timedelta(
                minutes=min(members.values())
            )
