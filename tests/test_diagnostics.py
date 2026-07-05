"""Tests for the diagnostics platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.components.diagnostics import REDACTED
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.incharge_availability.const import (
    CONF_RADIUS_KM,
    CONF_STATION_ID,
    DOMAIN,
)
from custom_components.incharge_availability.diagnostics import (
    async_get_config_entry_diagnostics,
)

STATION = {
    "id": "AB1234",
    "street": "Teststraat",
    "owner": "Tester",
    "connectorsData": {
        "connectors": [{"type": "Type2", "availableCount": 1, "count": 2}]
    },
}


async def test_diagnostics_redacts_location(hass: HomeAssistant) -> None:
    """The search coordinates are redacted; station data is kept."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AB1234",
        title="Teststraat",
        data={
            CONF_STATION_ID: "AB1234",
            CONF_LATITUDE: 52.0,
            CONF_LONGITUDE: 5.0,
            CONF_RADIUS_KM: 0.5,
        },
        options={},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.incharge_availability.InChargeApi"
    ) as api_cls:
        api_cls.return_value.async_station_by_id = AsyncMock(
            return_value=STATION
        )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"][CONF_LATITUDE] == REDACTED
    assert diagnostics["entry"]["data"][CONF_LONGITUDE] == REDACTED
    assert diagnostics["entry"]["data"][CONF_STATION_ID] == "AB1234"
    assert diagnostics["coordinator_data"]["available"] == 1
    assert diagnostics["last_update_success"] is True
