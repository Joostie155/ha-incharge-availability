"""Config flow: search for a charging station, then let the user pick one."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InChargeApi, InChargeApiError, parse_station
from .const import (
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEG_PER_KM,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)

# The map/location picker returns {"latitude", "longitude", "radius" (metres)}.
CONF_LOCATION = "location"


class InChargeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a Vattenfall InCharge charging station."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> InChargeOptionsFlow:
        """Return the options flow handler for this integration."""
        return InChargeOptionsFlow()

    def __init__(self) -> None:
        self._latitude: float | None = None
        self._longitude: float | None = None
        self._radius_km: float = DEFAULT_RADIUS_KM
        self._stations: dict[str, dict[str, Any]] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: choose a location + radius to search."""
        errors: dict[str, str] = {}
        if user_input is not None:
            location = user_input[CONF_LOCATION]
            self._latitude = location[CONF_LATITUDE]
            self._longitude = location[CONF_LONGITUDE]
            self._radius_km = max(location.get("radius", 500) / 1000, 0.1)

            api = InChargeApi(async_get_clientsession(self.hass))
            try:
                stations = await api.async_stations_near(
                    self._latitude, self._longitude, self._radius_km * DEG_PER_KM
                )
            except InChargeApiError:
                errors["base"] = "cannot_connect"
            else:
                self._stations = {s["id"]: s for s in stations}
                if not self._stations:
                    errors["base"] = "no_stations"
                else:
                    return await self.async_step_pick()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LOCATION,
                    default={
                        CONF_LATITUDE: self.hass.config.latitude,
                        CONF_LONGITUDE: self.hass.config.longitude,
                        "radius": DEFAULT_RADIUS_KM * 1000,
                    },
                ): selector.LocationSelector(
                    selector.LocationSelectorConfig(radius=True)
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: pick one of the found stations."""
        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            await self.async_set_unique_id(station_id)
            self._abort_if_unique_id_configured()

            station = parse_station(self._stations[station_id])
            return self.async_create_entry(
                title=station["street"] or station_id,
                data={
                    CONF_STATION_ID: station_id,
                    CONF_STATION_NAME: station["street"],
                    CONF_LATITUDE: self._latitude,
                    CONF_LONGITUDE: self._longitude,
                    CONF_RADIUS_KM: self._radius_km,
                },
            )

        options: list[selector.SelectOptionDict] = []
        for station_id, raw in self._stations.items():
            station = parse_station(raw)
            label = (
                f"{station['street']} · {station['owner']} · "
                f"{station['available']}/{station['total']} available"
            )
            options.append(
                selector.SelectOptionDict(value=station_id, label=label)
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="pick", data_schema=schema)


class InChargeOptionsFlow(OptionsFlow):
    """Let the user tune how often the station is polled."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the poll interval."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL_MINUTES, default=current
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_MINUTES,
                        max=MAX_SCAN_INTERVAL_MINUTES,
                        step=1,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
