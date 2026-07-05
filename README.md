# Vattenfall InCharge availability — Home Assistant integration

[![hacs][hacs-badge]][hacs-url]
[![Validate](https://github.com/Joostie155/ha-incharge-availability/actions/workflows/validate.yml/badge.svg)](https://github.com/Joostie155/ha-incharge-availability/actions/workflows/validate.yml)

A custom [Home Assistant][ha] integration that reports the **live availability**
of public EV charging stations, using the same data source the
[Vattenfall InCharge][incharge] map website itself shows.

You add a station through the UI (Settings → Devices & Services), and get a
sensor with the number of connectors currently free — handy for a dashboard
card or an automation that pings you when a spot in your street opens up.

> ⚠️ **Unofficial.** This project is not affiliated with, endorsed by, or
> supported by Vattenfall. It talks to an undocumented public endpoint that can
> change or break at any time. "Vattenfall" and "InCharge" are trademarks of
> their respective owners.

---

## Status

Early days — this is the **base skeleton**, built to grow step by step. What
works today:

- 🔍 Config-flow setup: pick a point + radius on a map, choose a station from
  the list found there.
- 📊 One sensor per station: `available` connectors (with `total`, `street`,
  `owner` and per-connector-type breakdown as attributes).
- 🔁 Polls every few minutes via a `DataUpdateCoordinator`.

See the [roadmap](#roadmap) for what's next.

## Installation (HACS)

**Quick add** — click the button, confirm your Home Assistant address, and the
repository opens straight inside HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Joostie155&repository=ha-incharge-availability&category=integration)

Then **Download**, restart Home Assistant, and add the integration:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=incharge_availability)

<details>
<summary>Manual steps (if the buttons don't work)</summary>

1. In HACS → ⋮ → **Custom repositories**, add
   `https://github.com/Joostie155/ha-incharge-availability` with category
   **Integration**.
2. Install **Vattenfall InCharge availability** and restart Home Assistant.
3. **Settings → Devices & Services → + Add Integration →** search for
   *Vattenfall InCharge availability*.

Fully manual install (no HACS): copy `custom_components/incharge_availability/`
into your Home Assistant `config/custom_components/` folder and restart.

</details>

> The buttons use [My Home Assistant](https://my.home-assistant.io/) — they open
> *your* instance in your browser; nothing is sent anywhere else.

## Configuration

Everything is done in the UI — there is nothing to put in `configuration.yaml`,
and no API key is required.

1. The setup dialog shows a map centred on your Home Assistant home location.
   Move the point and adjust the radius to cover the station(s) you care about.
2. Pick a station from the list. It becomes a device with an
   *Available connectors* sensor.
3. Repeat to add more stations (any operator that shows up on the InCharge map —
   not only Vattenfall's own poles).

## How it works

The InCharge map is a Google-Maps front-end backed by a small JSON API. This
integration uses two of its endpoints:

| Step | Endpoint | Purpose |
| ---- | -------- | ------- |
| 1 | `POST /api/v1/map/Stations/Coords/` | bounding box → exact station coordinates |
| 2 | `POST /api/v1/map/Stations/` | those coordinates → full objects with live availability |

Step 2 matches coordinates exactly, so we always feed it the coordinates from
step 1 and then select the station by its stable `id`. Availability comes from
`connectorsData.connectors[].availableCount`.

Please poll responsibly — the default interval is deliberately modest.

## Roadmap

- [x] `binary_sensor` "any connector free" per station
- [x] Configurable poll interval (options flow)
- [x] Test suite (config flow, options flow, setup/unload, parsing)
- [x] Diagnostics (redacted config-entry download)
- [x] Anchor entity ids on the station id (keep history across re-adds)
- [x] Dutch translation
- [ ] Brand assets + HACS default-repo submission

Contributions and issues welcome.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

## License

[MIT](LICENSE)

[ha]: https://www.home-assistant.io/
[incharge]: https://incharge.vattenfall.nl/ons-netwerk
[hacs]: https://hacs.xyz/
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
