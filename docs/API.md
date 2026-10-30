# Public interface

What this package promises. The major version changes when anything listed here is renamed or
removed; the [changelog](../CHANGELOG.md) says how the other kinds of change are versioned.
[COMMANDS.md](COMMANDS.md) explains each command; this page only names them.

## Commands

| Command | Parameter | Module |
|---|---|---|
| `EXHAUST_FAN`, `BED_FANS`, `EXTERNAL_PC` | `SPEED` | `fans.cfg` |
| `PART_COOLING` | `SPEED` | `fans.cfg` |
| `RESET_FANS` | none | `fans.cfg` |
| `CHAMBER` | `TEMP` | `chamber.cfg` |
| `LED_ON`, `LED_DIM`, `LED_OFF` | none | `leds.cfg` |
| `DUMP_FAN` | none | `dump_fan.cfg` |
| `MOTION_SENSOR`, `SWITCH_SENSOR` | `ENABLE` | `sensors.cfg` |
| `RELEASE_Z`, `RELEASE_XY` | none | `release_steppers.cfg` |
| `HARDWARE_CHECK` | none | `hardware_check.cfg` |
| `HOTEND_FAN_CHECK`, `FAN_STOPPAGE_ROUTINE` | none | `optional/fan_tach_monitor.cfg` |

`FAN_STOPPAGE_ROUTINE` is the one command a printer may override to change what happens when
the hotend fan stops.

## Roles

The variables of `_HARDWARE_VARS`, defined in `hardware_names.cfg`. A printer sets the ones it
needs in its own `_HARDWARE_VARS` section. The README table says what each refers to and who
reads it.

`chamber_heater`, `chamber_sensor`, `bed_heater`, `exhaust_fan`, `bed_fans`, `external_pc`,
`part_fan`, `hotend_fan`, `motion_sensor`, `switch_sensor`, `led_neopixels`, `led_pins`,
`release_xy_steppers`

## Variables a printer may set

| Macro | Variables |
|---|---|
| `LED_DIM` | `neopixel_level`, `pin_level` |
| `HOTEND_FAN_CHECK` | `check_seconds`, `max_consecutive_stops`, `min_rpm` (the monitor does nothing until a printer sets it) |
| `MOTION_SENSOR` | `fmotion_enabled` |
| `SWITCH_SENSOR` | `fswitch_enabled` |

`fmotion_enabled` and `fswitch_enabled` are not read by this package. A printer's pause macro
saves each sensor's state in them and its resume macro restores it.

## Variables a printer's macros may read

| Macro | Variable | Holds |
|---|---|---|
| `_HOTEND_FAN_STATE` | `target` | The hotend target that `FAN_STOPPAGE_ROUTINE` turned off, while it runs `PAUSE`. 0 at any other time. A `PAUSE` macro that saves the hotend target for `RESUME` reads it. |

## Delayed gcode ids

| Id | Module | Started by |
|---|---|---|
| `ENABLE_MOTION_SENSOR` | `sensors.cfg` | the printer, with `UPDATE_DELAYED_GCODE` |
| `HOTEND_FAN_MONITOR` | `optional/fan_tach_monitor.cfg` | itself, one second after Klipper starts |

## For other repositories

A repository that tests against this one finds the checkout beside itself, or at the path in
`HARDWARE_CONTROLS_PATH`. `HARDWARE_CONTROLS_ROOT` is read by the simulator and loads the
package configs from another checkout. These names stay as they are within a major version.

| Module in `tests/` | Names |
|---|---|
| `klipper_sim` | `HW_ROOT`, `HARDWARE_MODULES`, `module_path`, `State`, `wrap`, `default_state`, `Printer` |
| `config_lint` | `lint_file`, `lint` |
| `klippy_batch` | `ENV`, `SUPPORT_DIR`, `skip_unless_configured`, `delayed_gcode_as_macro`, `run_script`, `error_lines`, `run_script_files` |

- `Printer(hardware=True)` has the methods `load`, `run` and `execute`, and the attributes
  `state`, `templates`, `commands`, `messages`, `delays` and `idle_timeout`.
- `lint_file(path, check_includes=True, max_columns=100)` takes `max_columns=None` to turn the
  width check off. `lint(root, skip=())` lints every `.cfg` under a folder.
- `default_state()` describes the devices of `tests/klippy/printer.cfg`. Devices are only ever
  added to it.
- The real-firmware runner reads `KLIPPER_DIR`, `KLIPPY_DICT` and `KLIPPY_PYTHON`, and
  `KLIPPY_REQUIRED=1` turns a skipped run into an error.
- `tests/klippy/printer.cfg`, `hardware_names.cfg` and `assert.cfg` are the base configuration
  of every real-firmware run that uses `SUPPORT_DIR`.
