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

1. In HACS → ⋮ → **Custom repositories**, add
   `https://github.com/Joostie155/ha-incharge-availability` with category
   **Integration**.
2. Install **Vattenfall InCharge availability** and restart Home Assistant.
3. **Settings → Devices & Services → + Add Integration →** search for
   *Vattenfall InCharge availability*.

<sub>Manual install: copy `custom_components/incharge_availability/` into your
Home Assistant `config/custom_components/` folder and restart.</sub>

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

- [ ] `binary_sensor` "any connector free" per station
- [ ] Configurable poll interval (options flow)
- [ ] Diagnostics + proper unavailable handling
- [ ] Translations beyond English
- [ ] Tests + HACS default-repo submission

Contributions and issues welcome.

## License

[MIT](LICENSE)

[ha]: https://www.home-assistant.io/
[incharge]: https://incharge.vattenfall.nl/ons-netwerk
[hacs]: https://hacs.xyz/
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
