# Brand assets

Hand-drawn icon for the integration — a charge bolt with a green "a spot is
free" availability badge.

| File | Size | Use |
| ---- | ---- | --- |
| `icon.svg` | vector | source of truth; edit this |
| `icon.png` | 256×256 | standard integration icon |
| `icon@2x.png` | 512×512 | high-DPI / brands `icon.png` |

Colours: charge blue `#33A9EA → #0C68B0`, available green `#33D275 → #16A757`.

## Regenerate the PNGs

From this folder, after editing `icon.svg` (macOS, uses Quick Look):

```bash
qlmanage -t -s 512 -o . icon.svg && mv icon.svg.png icon@2x.png
qlmanage -t -s 256 -o . icon.svg && mv icon.svg.png icon.png
```

> Note: Home Assistant only shows this icon in its UI once it is submitted to
> the [home-assistant/brands](https://github.com/home-assistant/brands) repo
> under the `incharge_availability` domain. Until then these assets serve the
> README and act as the ready-to-submit source.
