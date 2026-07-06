"""Tests for setup, unload, batched coordinators, and the poll interval."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.incharge_availability.api import InChargeApiError
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
OTHER_STATION = {
    "id": "CD5678",
    "street": "Andere straat",
    "owner": "Tester",
    "connectorsData": {
        "connectors": [{"type": "CCS", "availableCount": 0, "count": 1}]
    },
}

API_PATH = "custom_components.incharge_availability.InChargeApi"


def _entry(station_id: str = "AB1234", **options) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=station_id,
        title="Teststraat",
        data={
            CONF_STATION_ID: station_id,
            CONF_LATITUDE: 52.0,
            CONF_LONGITUDE: 5.0,
            CONF_RADIUS_KM: 0.5,
        },
        options=options,
    )


def _patch_api(return_value):
    patcher = patch(API_PATH)
    api_cls = patcher.start()
    api_cls.return_value.async_stations_near = AsyncMock(return_value=return_value)
    return patcher, api_cls


async def test_setup_and_unload(hass: HomeAssistant) -> None:
    """A config entry sets up its coordinator and tears it down cleanly."""
    entry = _entry()
    entry.add_to_hass(hass)

    patcher, _ = _patch_api([STATION])
    try:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    finally:
        patcher.stop()

    assert entry.state is ConfigEntryState.LOADED
    hub = hass.data[DOMAIN]
    coordinator, station_id = hub.runtime[entry.entry_id]
    assert station_id == "AB1234"
    assert coordinator.data["AB1234"]["available"] == 1

    # Entities are keyed on the stable station id, not the volatile entry id,
    # so their history survives removing and re-adding the station. The
    # per-connector-type sensor is derived from the live payload.
    registry = er.async_get(hass)
    unique_ids = {
        e.unique_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    }
    assert unique_ids == {
        "AB1234_available",
        "AB1234_available_connectors",
        "AB1234_occupied_connectors",
        "AB1234_available_Type2",
    }

    assert await hass.config_entries.async_unload(entry.entry_id)
    # The last entry leaving drops the whole hub from hass.data.
    assert DOMAIN not in hass.data


async def test_scan_interval_option_is_applied(hass: HomeAssistant) -> None:
    """The coordinator honours the poll interval from the entry options."""
    entry = _entry(**{CONF_SCAN_INTERVAL_MINUTES: 7})
    entry.add_to_hass(hass)

    patcher, _ = _patch_api([STATION])
    try:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    finally:
        patcher.stop()

    coordinator, _ = hass.data[DOMAIN].runtime[entry.entry_id]
    assert coordinator.update_interval == timedelta(minutes=7)


async def test_entries_in_same_box_share_one_coordinator(
    hass: HomeAssistant,
) -> None:
    """Two stations from the same search box poll through one coordinator."""
    entry_a = _entry("AB1234", **{CONF_SCAN_INTERVAL_MINUTES: 10})
    entry_b = _entry("CD5678", **{CONF_SCAN_INTERVAL_MINUTES: 4})
    entry_a.add_to_hass(hass)
    entry_b.add_to_hass(hass)

    # Setting up the first entry sets up the whole component, so both entries
    # in the domain get loaded here.
    patcher, api_cls = _patch_api([STATION, OTHER_STATION])
    try:
        assert await hass.config_entries.async_setup(entry_a.entry_id)
        await hass.async_block_till_done()
    finally:
        patcher.stop()

    assert entry_a.state is ConfigEntryState.LOADED
    assert entry_b.state is ConfigEntryState.LOADED
    hub = hass.data[DOMAIN]
    coord_a, _ = hub.runtime[entry_a.entry_id]
    coord_b, _ = hub.runtime[entry_b.entry_id]

    # Same coordinator object -> one poll feeds both stations.
    assert coord_a is coord_b
    # The single box fetch was made once, not once per entry.
    assert api_cls.return_value.async_stations_near.await_count == 1
    # The shared interval tightens to the most eager sharer (4 min < 10 min).
    assert coord_a.update_interval == timedelta(minutes=4)

    # Dropping one entry keeps the coordinator alive for the other and relaxes
    # the interval back to that entry's setting.
    assert await hass.config_entries.async_unload(entry_b.entry_id)
    assert entry_b.entry_id not in hub.runtime
    assert coord_a.update_interval == timedelta(minutes=10)
    assert not hub.is_empty


async def test_api_error_marks_entities_unavailable(hass: HomeAssistant) -> None:
    """A failing poll must degrade to 'unavailable', not raise."""
    entry = _entry()
    entry.add_to_hass(hass)

    with patch(API_PATH) as api_cls:
        # First refresh succeeds so the entry loads and entities register...
        api_cls.return_value.async_stations_near = AsyncMock(
            return_value=[STATION]
        )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert hass.states.get("sensor.teststraat_available_connectors").state == "1"

        # ...then the endpoint starts failing (e.g. 403 / rate limit).
        coordinator, _ = hass.data[DOMAIN].runtime[entry.entry_id]
        api_cls.return_value.async_stations_near = AsyncMock(
            side_effect=InChargeApiError("boom")
        )
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    assert coordinator.last_update_success is False
    assert (
        hass.states.get("sensor.teststraat_available_connectors").state
        == "unavailable"
    )
    assert hass.states.get("binary_sensor.teststraat_available").state == "unavailable"
