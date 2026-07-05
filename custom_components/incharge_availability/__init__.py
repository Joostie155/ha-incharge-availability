"""The Vattenfall InCharge availability integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InChargeApi
from .const import CONF_RADIUS_KM, CONF_STATION_ID, DEFAULT_RADIUS_KM, DOMAIN
from .coordinator import InChargeCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a charging station from a config entry."""
    api = InChargeApi(async_get_clientsession(hass))
    coordinator = InChargeCoordinator(
        hass,
        api,
        entry.data[CONF_STATION_ID],
        entry.data[CONF_LATITUDE],
        entry.data[CONF_LONGITUDE],
        entry.data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
