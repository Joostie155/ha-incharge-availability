"""Minimal async client for Vattenfall InCharge's public map API.

This talks to the same endpoints the incharge.vattenfall.nl map itself uses to
show live charging-station availability. It is an UNOFFICIAL, undocumented API
and may change or disappear without notice.

Lookup is two steps, because the ``/Stations/`` endpoint matches coordinates
*exactly* (a rounded coordinate returns an empty station):

  1. ``POST /api/v1/map/Stations/Coords/``  body ``{bounds, filters}``
       -> ``[{lat, lng}, ...]`` — the canonical coordinates of every station
          inside the bounding box.
  2. ``POST /api/v1/map/Stations/``  body ``[{lat, lng}, ...]``
       -> full station objects, including live availability.

We then pick out a station by its stable ``id`` (e.g. ``"AB1234"``).
"""

from __future__ import annotations

from typing import Any

import aiohttp

API_BASE = "https://incharge.vattenfall.nl/api/v1/map"

# The map's WAF requires a same-origin Origin/Referer, otherwise it returns 403.
_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://incharge.vattenfall.nl",
    "Referer": "https://incharge.vattenfall.nl/ons-netwerk",
    "User-Agent": "home-assistant-incharge-availability",
}

# The map always sends this (empty) filter block; keep it for parity.
_FILTERS: dict[str, Any] = {
    "permanentFilter": {
        "countries": [],
        "userAccountNumbers": [],
        "priceCategories": [],
    }
}

_TIMEOUT = aiohttp.ClientTimeout(total=20)


class InChargeApiError(Exception):
    """Raised when the InCharge API cannot be reached or returns junk."""


class InChargeApi:
    """Thin async wrapper around the InCharge public map endpoints."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _post(self, path: str, body: Any) -> Any:
        try:
            async with self._session.post(
                f"{API_BASE}/{path}/",
                json=body,
                headers=_HEADERS,
                timeout=_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise InChargeApiError(str(err)) from err

    async def async_stations_near(
        self, latitude: float, longitude: float, margin_deg: float
    ) -> list[dict[str, Any]]:
        """Return the raw station objects within a small box around a point."""
        bounds = {
            "north": latitude + margin_deg,
            "south": latitude - margin_deg,
            "east": longitude + margin_deg,
            "west": longitude - margin_deg,
        }
        coords = await self._post(
            "Stations/Coords", {"bounds": bounds, "filters": _FILTERS}
        )
        if not coords:
            return []
        stations = await self._post("Stations", coords)
        return [s for s in stations if isinstance(s, dict) and s.get("id")]

    async def async_station_by_id(
        self,
        station_id: str,
        latitude: float,
        longitude: float,
        margin_deg: float,
    ) -> dict[str, Any] | None:
        """Return one station by its stable id, or None if not found nearby."""
        for station in await self.async_stations_near(
            latitude, longitude, margin_deg
        ):
            if station.get("id") == station_id:
                return station
        return None


def parse_station(raw: dict[str, Any]) -> dict[str, Any]:
    """Reduce a raw station object to the fields this integration exposes.

    InCharge reports availability aggregated per connector *type*
    (``availableCount`` of ``count``), not per physical socket.
    """
    connector_data = raw.get("connectorsData") or {}
    groups = connector_data.get("connectors") or []
    total = sum(int(g.get("count") or 0) for g in groups)
    if not total:
        total = int(connector_data.get("totalCount") or 0)
    available = sum(int(g.get("availableCount") or 0) for g in groups)
    return {
        "id": raw.get("id"),
        "street": raw.get("street"),
        "owner": raw.get("owner"),
        "available": available,
        "total": total,
        "connector_types": [
            {
                "type": g.get("type"),
                "available": int(g.get("availableCount") or 0),
                "count": int(g.get("count") or 0),
            }
            for g in groups
        ],
    }
