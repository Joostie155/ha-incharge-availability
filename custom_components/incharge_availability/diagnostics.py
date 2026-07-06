"""Diagnostics support for the Vattenfall InCharge availability integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import InChargeHub

# The search point can sit close to the user's home, so keep it out of dumps
# that end up attached to public bug reports. The station data itself is public.
TO_REDACT = {CONF_LATITUDE, CONF_LONGITUDE}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hub: InChargeHub = hass.data[DOMAIN]
    coordinator, station_id = hub.runtime[entry.entry_id]
    region = coordinator.data or {}
    return {
        "entry": {
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": dict(entry.options),
        },
        "coordinator_data": region.get(station_id),
        "stations_in_region": len(region),
        "last_update_success": coordinator.last_update_success,
    }
