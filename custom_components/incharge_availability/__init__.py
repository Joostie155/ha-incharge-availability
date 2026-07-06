"""The Vattenfall InCharge availability integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InChargeApi
from .const import (
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_STATION_ID,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .coordinator import InChargeHub

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a charging station from a config entry."""
    hub = hass.data.get(DOMAIN)
    if hub is None:
        api = InChargeApi(async_get_clientsession(hass))
        hub = InChargeHub(hass, api)
        hass.data[DOMAIN] = hub

    await hub.async_setup_entry(
        entry.entry_id,
        entry.data[CONF_STATION_ID],
        entry.data[CONF_LATITUDE],
        entry.data[CONF_LONGITUDE],
        entry.data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
        entry.options.get(
            CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES
        ),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change (e.g. new poll interval)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hub: InChargeHub = hass.data[DOMAIN]
        hub.async_unload_entry(
            entry.entry_id,
            entry.data[CONF_LATITUDE],
            entry.data[CONF_LONGITUDE],
            entry.data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
        )
        if hub.is_empty:
            hass.data.pop(DOMAIN)
    return unloaded
