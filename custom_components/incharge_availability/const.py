"""Constants for the Vattenfall InCharge availability integration."""

from __future__ import annotations

DOMAIN = "incharge_availability"

# Config entry keys (CONF_LATITUDE / CONF_LONGITUDE come from homeassistant.const).
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_RADIUS_KM = "radius_km"

# Options entry keys.
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

# Defaults.
DEFAULT_RADIUS_KM = 0.5
DEFAULT_SCAN_INTERVAL_MINUTES = 5

# Bounds for the user-configurable poll interval (options flow).
MIN_SCAN_INTERVAL_MINUTES = 1
MAX_SCAN_INTERVAL_MINUTES = 60

# State attribute keys.
ATTR_TOTAL = "total"
ATTR_OCCUPIED = "occupied"
ATTR_STREET = "street"
ATTR_OWNER = "owner"
ATTR_CITY = "city"
ATTR_MAX_POWER_KW = "max_power_kw"
ATTR_STATION_ID = "station_id"
ATTR_CONNECTOR_TYPES = "connector_types"

# Degrees of latitude per kilometre — good enough to build a small search box.
DEG_PER_KM = 1.0 / 111.0
