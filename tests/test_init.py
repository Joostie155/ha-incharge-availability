"""Tests for setup, unload, and the options-driven poll interval."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.incharge_availability.const import (
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_STATION_ID,
    DOMAIN,
)

STATION = {
    "id": "AB1234",
    "street": "Teststraat",
    "owner": "Tester",
    "connectorsData": {
        "connectors": [{"type": "Type2", "availableCount": 1, "count": 2}]
    },
}


def _entry(**options) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="AB1234",
        title="Teststraat",
        data={
            CONF_STATION_ID: "AB1234",
            CONF_LATITUDE: 52.0,
            CONF_LONGITUDE: 5.0,
            CONF_RADIUS_KM: 0.5,
        },
        options=options,
    )


async def test_setup_and_unload(hass: HomeAssistant) -> None:
    """A config entry sets up its coordinator and tears it down cleanly."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.incharge_availability.InChargeApi"
    ) as api_cls:
        api_cls.return_value.async_station_by_id = AsyncMock(
            return_value=STATION
        )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.data["available"] == 1

    # Entities are keyed on the stable station id, not the volatile entry id,
    # so their history survives removing and re-adding the station.
    registry = er.async_get(hass)
    unique_ids = {
        e.unique_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    }
    assert unique_ids == {"AB1234_available", "AB1234_available_connectors"}

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_scan_interval_option_is_applied(hass: HomeAssistant) -> None:
    """The coordinator honours the poll interval from the entry options."""
    entry = _entry(**{CONF_SCAN_INTERVAL_MINUTES: 7})
    entry.add_to_hass(hass)

    with patch(
        "custom_components.incharge_availability.InChargeApi"
    ) as api_cls:
        api_cls.return_value.async_station_by_id = AsyncMock(
            return_value=STATION
        )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval == timedelta(minutes=7)
