"""Unit tests for the pure API helpers (no Home Assistant needed)."""

from __future__ import annotations

from custom_components.incharge_availability.api import parse_station


def test_parse_station_sums_connector_groups() -> None:
    """Availability and total are summed across connector-type groups."""
    raw = {
        "id": "AB1234",
        "street": "Teststraat",
        "city": "Utrecht",
        "owner": "Tester",
        "maxPower": 17250,
        "connectorsData": {
            "connectors": [
                {"type": "Type2", "availableCount": 1, "count": 2},
                {"type": "CCS", "availableCount": 0, "count": 1},
            ]
        },
    }

    result = parse_station(raw)

    assert result["id"] == "AB1234"
    assert result["street"] == "Teststraat"
    assert result["city"] == "Utrecht"
    assert result["available"] == 1
    assert result["total"] == 3
    # 3 total, 1 free -> 2 occupied (charging or out of service).
    assert result["occupied"] == 2
    # maxPower is watts; exposed as kW.
    assert result["max_power_kw"] == 17.2
    assert len(result["connector_types"]) == 2


def test_parse_station_falls_back_to_total_count() -> None:
    """When no per-type counts exist, fall back to ``totalCount``."""
    raw = {"id": "X", "connectorsData": {"totalCount": 4}}

    result = parse_station(raw)

    assert result["total"] == 4
    assert result["available"] == 0
    assert result["occupied"] == 4


def test_parse_station_handles_missing_data() -> None:
    """A station object with no connector data degrades gracefully."""
    result = parse_station({"id": "Y"})

    assert result["total"] == 0
    assert result["available"] == 0
    assert result["occupied"] == 0
    assert result["max_power_kw"] is None
    assert result["connector_types"] == []
