# Klipper Hardware Controls

[![Hardware template checks](https://github.com/IdleStep/Klipper-Hardware-Controls/actions/workflows/templates.yml/badge.svg)](https://github.com/IdleStep/Klipper-Hardware-Controls/actions/workflows/templates.yml)

Reusable hardware commands (fans, chamber heater, LEDs, filament sensors,
stepper release) for Klipper and Kalico configurations. Klipper-Configs and
[Klipper-Chamber-Cooldown](https://github.com/IdleStep/Klipper-Chamber-Cooldown)
build on it; it depends only on standard Klipper macros and `[respond]`.

Public command API: **version 1**. Commands, parameters and `_HARDWARE_VARS`
names stay compatible within version 1. See the [changelog](CHANGELOG.md).

Tested with Klipper (Jinja 2.11) and Kalico (Jinja 3.1), loaded in the real firmware, at
the revisions pinned in [`templates.yml`](.github/workflows/templates.yml) and every week
against their newest. Older firmware is not tested.

## Install

Clone into `~/printer_data/config`, then include once:

```sh
cd ~/printer_data/config
git clone https://github.com/IdleStep/Klipper-Hardware-Controls.git
```

```ini
[include Klipper-Hardware-Controls/hardware.cfg]
[include hardware_names.cfg]
```

The second line is your own copy of `hardware_names.cfg`, outside the checkout, that names
your devices (see [Configuration](#configuration)). Without it the package controls only the
stock devices: the bed heater, the part fan `fan` and the X and Y steppers.

Or include `hardware_names.cfg` followed by only the modules you need:

| Module | Commands |
|---|---|
| `fans.cfg` | EXHAUST_FAN, BED_FANS, EXTERNAL_PC, PART_COOLING, RESET_FANS |
| `chamber.cfg` | CHAMBER |
| `leds.cfg` | LED_ON, LED_DIM, LED_OFF |
| `dump_fan.cfg` | DUMP_FAN |
| `sensors.cfg` | MOTION_SENSOR, SWITCH_SENSOR, delayed ENABLE_MOTION_SENSOR |
| `release_steppers.cfg` | RELEASE_Z, RELEASE_XY |

Chamber cooldown needs `hardware_names.cfg`, `fans.cfg` and `chamber.cfg`. Never load
the bundle and individual modules together.

## Configuration

Physical devices (pins, sensor types, heater verification, power limits) stay in
your printer configuration. This package only needs to know their names, set in
`_HARDWARE_VARS`. `hardware_names.cfg` holds the defaults, which are off for every role
that depends on your own devices. Copy it outside this checkout, next to your `printer.cfg`,
keep only the roles your printer sets, give them your devices' names and include it after
the package. Klipper merges the two sections and the later value wins.

| Variable | Default | Refers to |
|---|---|---|
| `chamber_heater` | `""` | `[heater_generic NAME]` |
| `chamber_sensor` | `""` | full object name, read when there is no chamber heater |
| `bed_heater` | `"heater_bed"` | full object name |
| `exhaust_fan`, `bed_fans`, `external_pc` | `""` | `[fan_generic NAME]` |
| `part_fan` | `"fan"` | `fan` (M106) or `fan_generic NAME` |
| `hotend_fan` | `"hotend_fan"` | `[heater_fan NAME]`, watched by the optional tachometer monitor |
| `motion_sensor`, `switch_sensor` | `""` | `[filament_motion_sensor NAME]`, `[filament_switch_sensor NAME]` |
| `led_neopixels`, `led_pins` | `[]` | `[neopixel NAME]`, `[output_pin NAME]` |
| `release_xy_steppers` | `["stepper_x", "stepper_y"]` | stepper sections |

An empty string or list disables a role. Devices that are not configured are skipped
without an error.

## Commands

| Command | Parameters and behavior |
|---|---|
| EXHAUST_FAN, BED_FANS, EXTERNAL_PC | `SPEED=0.0` to `1.0` (default 0, which stops the fan). Anything else, including text, leaves the fan as it is and reports `Fan speed must be between 0.0 and 1.0`. The error is reported, not raised, so it does not abort the macro or print that sent it. |
| PART_COOLING | `SPEED=0.0` to `1.0`, or `1.1` to `100` percent (default 0). Any other value turns the fan off and reports `Invalid PART_COOLING value`, so a slicer typo cannot abort a print. Speeds below the fan's `min_power` (or `off_below` when `min_power` is unset) turn it off. |
| RESET_FANS | Stops every configured controlled fan role. |
| CHAMBER | `TEMP=` chamber heater target in °C (default 0, which turns the heater off). Text or a negative value turns the heater off and reports `Invalid CHAMBER value`. Klipper itself refuses a target above the heater's `max_temp`. |
| LED_ON, LED_OFF, LED_DIM | Configured neopixel and output-pin groups. LED_DIM uses the `neopixel_level` and `pin_level` variables of `[gcode_macro LED_DIM]` (default 0.3 each); override them in a file included after the package. |
| DUMP_FAN | Prints the configured part fan's status. |
| MOTION_SENSOR, SWITCH_SENSOR | `ENABLE=0` or `1` (default 1). Anything else, including text, leaves the sensor as it is and reports `MOTION_SENSOR ENABLE must be 0 or 1`, so a typo cannot disable runout detection. |
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

MOTION_SENSOR and SWITCH_SENSOR also carry `fmotion_enabled` and
`fswitch_enabled`. This package does not read them: they are there for PAUSE
macros to save each sensor's state and for RESUME macros to restore it.

## Optional fan tachometer monitor

`optional/fan_tach_monitor.cfg` watches the hotend fan's tachometer. It is excluded
from `hardware.cfg`. Include it only on printers with a `[heater_fan]` that has a
`tachometer_pin` (`hotend_fan` unless you name another, see below):

```ini
[include Klipper-Hardware-Controls/optional/fan_tach_monitor.cfg]
```

It starts one second after Klipper starts and checks every three seconds. After
three consecutive readings below 8000 RPM while the hotend is hot, it pauses the
print and turns the hotend off. If the print is already paused, the hotend is
still turned off. The check is skipped when the fan is missing or reports no RPM, so a
misconfigured fan cannot cause false pauses; the console says so once, so a monitor that
watches nothing is not silent.

The fan is the `hotend_fan` role of `_HARDWARE_VARS`, the name after the section type, so
`"nozzle_fan"` for `[heater_fan nozzle_fan]`. The limits are the `min_rpm`,
`max_consecutive_stops` and `check_seconds` variables of `[gcode_macro HOTEND_FAN_CHECK]`;
override them in a local file included after the monitor. To change what happens on a
stoppage, override `FAN_STOPPAGE_ROUTINE`. The idea comes from the fan tach monitor in
Andrew Ellis's Print-Tuning-Guide; this file is written for this package.

## Updates and rollback

Add this to `moonraker.conf`. It follows tagged releases (`channel: stable`); use
`channel: dev` to follow `main`.

```ini
[update_manager Klipper-Hardware-Controls]
type: git_repo
channel: stable
path: ~/printer_data/config/Klipper-Hardware-Controls
origin: https://github.com/IdleStep/Klipper-Hardware-Controls.git
primary_branch: main
is_system_service: False
managed_services: klipper
```

Update and restart only while the printer is idle, keep overrides outside the
checkout, and record the tested revision for each printer. To roll back, check
out the previous tag and restart. The [changelog](CHANGELOG.md) says what each tag
changes.

## Tests

```sh
pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

- `tests/klipper_sim.py` renders the macros and simulates the commands they emit.
  Klipper-Chamber-Cooldown and Klipper-Configs reuse it. It includes
  `tests/klippy/hardware_names.cfg`, the test printers' own copy, after the
  package, as a printer does.
- `tests/config_lint.py` checks every `.cfg` for parse errors, broken includes,
  tabs, trailing whitespace, malformed `RESPOND` messages, missing macro
  descriptions and `gcode_macro` or `delayed_gcode` options that stock Klipper
  does not read.
- `tests/test_klippy.py` loads the package in real Klipper and Kalico without
  hardware and runs `tests/klippy/*.gcode`, which assert fan speeds, heater
  targets and the pause state after the commands. It is skipped unless
  `KLIPPER_DIR`, `KLIPPY_DICT` and `KLIPPY_PYTHON` are set; the CI workflow shows
  how to build them.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Report a safety problem as described in
[SECURITY.md](SECURITY.md).

## Style

Conventions for the config files, messages and tests, shared with
Klipper-Chamber-Cooldown and Klipper-Configs, are in [docs/STYLE.md](docs/STYLE.md).

## License

GPL-3.0.
