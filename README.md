# Klipper Hardware Controls

Reusable hardware commands (fans, chamber heater, LEDs, filament sensors,
stepper release) for Klipper and Kalico configurations. Klipper-Configs and
[Klipper-CHAMBER_COOLDOWN](https://github.com/IdleStep/Klipper-CHAMBER_COOLDOWN)
build on it; it depends only on standard Klipper macros and `[respond]`.

Public command API: **version 1**. Commands, parameters and `_HARDWARE_VARS`
names stay compatible within version 1. See the [changelog](CHANGELOG.md).

## Install

Clone into `~/printer_data/config/Klipper-Hardware-Controls`, then include once:

```ini
[include Klipper-Hardware-Controls/hardware.cfg]
[include hardware-local.cfg]
```

Or include `settings.cfg` followed by only the modules you need:

| Module | Commands |
|---|---|
| `fans.cfg` | EXHAUST_FAN, BED_FANS, EXTERNAL_PC, PART_COOLING, RESET_FANS |
| `chamber.cfg` | CHAMBER |
| `leds.cfg` | LED_ON, LED_DIM, LED_OFF |
| `dump_fan.cfg` | DUMP_FAN |
| `sensors.cfg` | MOTION_SENSOR, SWITCH_SENSOR, delayed ENABLE_MOTION_SENSOR |
| `release_steppers.cfg` | RELEASE_Z, RELEASE_XY |

Chamber cooldown needs `settings.cfg`, `fans.cfg` and `chamber.cfg`. Never load
the bundle and individual modules together.

## Configuration

Physical devices (pins, sensor types, heater verification, power limits) stay in
your printer configuration. This package only needs to know their names, set in
`_HARDWARE_VARS` (`settings.cfg`). Copy
[`examples/hardware-local.cfg`](examples/hardware-local.cfg) outside this checkout,
keep only the values that differ and include it after the package.

| Variable | Default | Refers to |
|---|---|---|
| `chamber_heater` | `"chamber"` | `[heater_generic NAME]` |
| `chamber_sensor` | `"heater_generic chamber"` | full object name, read when there is no chamber heater |
| `bed_heater` | `"heater_bed"` | full object name |
| `exhaust_fan`, `bed_fans`, `external_pc` | role names | `[fan_generic NAME]` |
| `part_fan` | `"fan"` | `fan` (M106) or `fan_generic NAME` |
| `motion_sensor`, `switch_sensor` | role names | `[filament_motion_sensor NAME]`, `[filament_switch_sensor NAME]` |
| `led_neopixels`, `led_pins` | lists | `[neopixel NAME]`, `[output_pin NAME]` |
| `led_dim`, `led_pin_dim` | `0.3098`, `0.33` | LED_DIM levels |
| `release_xy_steppers` | `["stepper_x", "stepper_y"]` | stepper sections |

An empty string disables a role. Devices that are not configured are skipped
without an error.

## Commands

| Command | Parameters and behavior |
|---|---|
| EXHAUST_FAN, BED_FANS, EXTERNAL_PC | `SPEED=0.0` to `1.0`. Anything else, including text, is an error and nothing is sent. |
| PART_COOLING | `SPEED=0.0` to `1.0`, or `1.1` to `100` percent. Any other value turns the fan off and reports `invalid PART_COOLING value`, so a slicer typo cannot abort a print. Speeds below the fan's `min_power` (or `off_below` when `min_power` is unset) turn it off. |
| RESET_FANS | Stops every configured controlled fan role. |
| CHAMBER | `TEMP=` chamber heater target in °C. |
| LED_ON, LED_OFF, LED_DIM | Configured neopixel and output-pin groups. |
| DUMP_FAN | Prints the configured part fan's status. |
| MOTION_SENSOR, SWITCH_SENSOR | `ENABLE=0` or `1` (default 1). |
| RELEASE_Z | Runs `M84 Z`. Stock Klipper disables **all** motors for this. |
| RELEASE_XY | Disables the configured XY steppers individually. |

Stepper release never runs automatically. Disabling individual steppers does not
clear homing; rehome after moving a disabled axis by hand.

## Sensor scheduling

`sensors.cfg` defines an inert callback with no `initial_duration`:

```ini
[delayed_gcode ENABLE_MOTION_SENSOR]
gcode:
  MOTION_SENSOR ENABLE=1
```

The printer workflow decides when to schedule it, for example
`UPDATE_DELAYED_GCODE ID=ENABLE_MOTION_SENSOR DURATION=60`. Including the module
does not change sensor state.

## Optional fan tachometer monitor

`optional/fan_tach_monitor.cfg` is the Andrew Ellis / alch3my monitor, excluded
from `hardware.cfg`. Include it only on printers with `[heater_fan hotend_fan]`
and a `tachometer_pin`:

```ini
[include Klipper-Hardware-Controls/optional/fan_tach_monitor.cfg]
```

It starts one second after Klipper starts and checks every three seconds. After
three consecutive readings below 8000 RPM while the hotend is hot, it pauses the
print and turns the hotend off. The check is skipped when `hotend_fan` is missing
or reports no RPM, so a misconfigured fan cannot cause false pauses.

## Updates and rollback

Add [`examples/moonraker.conf`](examples/moonraker.conf) to `moonraker.conf`. It
follows tagged releases (`channel: stable`); use `channel: dev` to follow `main`.
Update and restart only while the printer is idle, keep overrides outside the
checkout, and record the tested revision for each printer. To roll back, check
out the previous tag and restart. Moving from the old Klipper-Configs helpers is
covered in [docs/MIGRATION.md](docs/MIGRATION.md).

## Tests

```sh
pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

- `tests/klipper_sim.py` renders the macros and simulates the commands they emit.
  Klipper-CHAMBER_COOLDOWN and Klipper-Configs reuse it.
- `tests/config_lint.py` checks every `.cfg` for parse errors, broken includes,
  tabs, trailing whitespace, malformed `RESPOND` messages and missing macro
  descriptions.
- `tests/test_klippy.py` loads the package in real Klipper and Kalico without
  hardware and runs `tests/klippy/*.gcode`. It is skipped unless `KLIPPER_DIR`,
  `KLIPPY_DICT` and `KLIPPY_PYTHON` are set; the CI workflow shows how to build
  them.

## License

GPL-3.0. The optional monitor keeps its upstream attribution.
