"""Tests for the config and options flows."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
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

LOCATION_INPUT = {
    "location": {CONF_LATITUDE: 52.0, CONF_LONGITUDE: 5.0, "radius": 500}
}

API_PATH = "custom_components.incharge_availability.config_flow.InChargeApi"


async def test_full_flow_creates_entry(hass: HomeAssistant) -> None:
    """Location step → pick step → entry, with a station found nearby."""
    with patch(API_PATH) as api_cls:
        api_cls.return_value.async_stations_near = AsyncMock(
            return_value=[STATION]
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCATION_INPUT
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "pick"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_STATION_ID: "AB1234"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Teststraat"
    assert result["data"][CONF_STATION_ID] == "AB1234"


async def test_flow_aborts_on_duplicate(hass: HomeAssistant) -> None:
    """Re-adding the same station id aborts as already_configured."""
    MockConfigEntry(
        domain=DOMAIN, unique_id="AB1234", data={CONF_STATION_ID: "AB1234"}
    ).add_to_hass(hass)

    with patch(API_PATH) as api_cls:
        api_cls.return_value.async_stations_near = AsyncMock(
            return_value=[STATION]
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCATION_INPUT
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_STATION_ID: "AB1234"}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_flow_shows_error_when_api_unreachable(
    hass: HomeAssistant,
) -> None:
    """An API error on search surfaces a cannot_connect form error."""
    with patch(API_PATH) as api_cls:
        api_cls.return_value.async_stations_near = AsyncMock(
            side_effect=InChargeApiError("boom")
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCATION_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_shows_error_when_no_stations(hass: HomeAssistant) -> None:
    """An empty search result surfaces a no_stations form error."""
    with patch(API_PATH) as api_cls:
        api_cls.return_value.async_stations_near = AsyncMock(return_value=[])
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], LOCATION_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_stations"}


async def test_options_flow_updates_interval(hass: HomeAssistant) -> None:
    """The options flow stores a new poll interval."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AB1234",
        data={
            CONF_STATION_ID: "AB1234",
            CONF_LATITUDE: 52.0,
            CONF_LONGITUDE: 5.0,
            CONF_RADIUS_KM: 0.5,
        },
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL_MINUTES: 10}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL_MINUTES] == 10
