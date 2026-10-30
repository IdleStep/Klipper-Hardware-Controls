# Klipper Hardware Controls

[![Hardware template checks](https://github.com/IdleStep/Klipper-Hardware-Controls/actions/workflows/templates.yml/badge.svg)](https://github.com/IdleStep/Klipper-Hardware-Controls/actions/workflows/templates.yml)

Fan, chamber heater, LED, filament sensor and stepper commands for Klipper and Kalico, driven by
a list of your device names.

You name your devices once. After that, `EXHAUST_FAN SPEED=0.5`, `CHAMBER TEMP=60` and `LED_DIM`
work in any macro, and a command whose device you did not name does nothing. Pins, sensor types
and heater settings stay in your own printer configuration.
[Klipper-Chamber-Cooldown](https://github.com/IdleStep/Klipper-Chamber-Cooldown) builds on this
package.

The major version is the version of the public interface. Only a major release renames or
removes a command, a parameter, a role or a variable you set. [docs/API.md](docs/API.md) lists
that interface and the [changelog](CHANGELOG.md) lists every release.

## Requirements

- Klipper v0.12.0 or newer, or Kalico v2026.01.00 or newer. The real-firmware tests passed on
  both releases, and CI runs them on newer revisions every week.
- A `[respond]` section in your `printer.cfg`. The commands use it to print to the console.

## Install

1. **Clone** into your configuration folder:

   ```sh
   cd ~/printer_data/config
   git clone https://github.com/IdleStep/Klipper-Hardware-Controls.git
   ```

2. **Include** the package in `printer.cfg`, then your own names file after it:

   ```ini
   # The package: a file in the folder you cloned.
   [include Klipper-Hardware-Controls/hardware.cfg]
   # Your names file: a different file, next to printer.cfg. You create it below.
   [include hardware_names.cfg]
   ```

   `hardware.cfg` includes every module except the optional fan monitor.

   Two files are called `hardware_names.cfg`. The one inside `Klipper-Hardware-Controls/` holds
   the defaults, with every role off, and `hardware.cfg` includes it for you. The other is your
   own copy in your configuration folder, where you name your devices; see
   [Name your devices](#name-your-devices). Klipper looks for an include in the folder of the
   file that contains it. That is why `printer.cfg` needs the folder name for the package and
   none for your file.

   To load only some modules, include the package's `hardware_names.cfg` yourself, then the
   modules, then your own names file. This example has what chamber cooldown needs:

   ```ini
   # The package's defaults, then the modules you want.
   [include Klipper-Hardware-Controls/hardware_names.cfg]
   [include Klipper-Hardware-Controls/fans.cfg]
   [include Klipper-Hardware-Controls/chamber.cfg]
   # Your own names file, next to printer.cfg.
   [include hardware_names.cfg]
   ```

   | Module | Commands |
   |---|---|
   | `fans.cfg` | EXHAUST_FAN, BED_FANS, EXTERNAL_PC, PART_COOLING, RESET_FANS |
   | `chamber.cfg` | CHAMBER |
   | `leds.cfg` | LED_ON, LED_DIM, LED_OFF |
   | `dump_fan.cfg` | DUMP_FAN |
   | `sensors.cfg` | MOTION_SENSOR, SWITCH_SENSOR |
   | `release_steppers.cfg` | RELEASE_Z, RELEASE_XY |
   | `hardware_check.cfg` | HARDWARE_CHECK |

   Every module reads the roles, so include the package's `hardware_names.cfg` and put your own
   after it. A command from a module you did not include is an unknown command. Including a
   module that `hardware.cfg` already includes does no harm.

3. **Restart** Klipper: run `RESTART` in the console.

## Name your devices

Copy the package's [`hardware_names.cfg`](hardware_names.cfg) next to your `printer.cfg`, keep
only the roles your printer needs, and give each the name of your device. For a printer with a
`[heater_generic chamber]` and a `[fan_generic exhaust_fan]`:

```ini
[gcode_macro _HARDWARE_VARS]
variable_chamber_heater: "chamber"
variable_exhaust_fan: "exhaust_fan"
```

Include your file after the package. Klipper merges the two `_HARDWARE_VARS` sections and the
later value wins, so a copy included before the package is overwritten by its empty roles. An
empty string or list turns a role off. Without your names file, only the part fan `fan` and the
X and Y steppers are controlled.

| Role | Default | Names | Used by |
|---|---|---|---|
| `chamber_heater` | `""` | `[heater_generic NAME]` | CHAMBER, Klipper-Chamber-Cooldown |
| `chamber_sensor` | `""` | full object name, read when there is no chamber heater | Klipper-Chamber-Cooldown |
| `bed_heater` | `"heater_bed"` | full object name | Klipper-Chamber-Cooldown |
| `exhaust_fan`, `bed_fans`, `external_pc` | `""` | `[fan_generic NAME]` | the command of the same name, Klipper-Chamber-Cooldown |
| `part_fan` | `"fan"` | `fan` for `[fan]`, or `fan_generic NAME` | PART_COOLING, DUMP_FAN |
| `hotend_fan` | `"hotend_fan"` | `[heater_fan NAME]` | the optional fan monitor |
| `motion_sensor`, `switch_sensor` | `""` | `[filament_motion_sensor NAME]`, `[filament_switch_sensor NAME]` | MOTION_SENSOR, SWITCH_SENSOR |
| `led_neopixels`, `led_pins` | `[]` | `[neopixel NAME]`, `[output_pin NAME]` | LED_ON, LED_DIM, LED_OFF |
| `release_xy_steppers` | `["stepper_x", "stepper_y"]` | stepper sections | RELEASE_XY |

## See it work

Run `HARDWARE_CHECK` in the console. It changes nothing and prints one line per role:

```
📃 chamber_heater - heater_generic chamber found
📃 chamber_sensor - off
📃 bed_heater - heater_bed found
📃 exhaust_fan - fan_generic exhaust_fan found
...
📃 Hardware check found nothing to fix
```

A `⚠️` line means a name matches no device. Fix it in your `hardware_names.cfg`, run `RESTART`
and check again.

Then run `EXHAUST_FAN SPEED=0.5`. The fan runs at half speed. A working command prints no
reply, so watch the fan or its speed in your web interface. `RESET_FANS` stops it.

## Commands

| Command | What it does | Parameter |
|---|---|---|
| EXHAUST_FAN, BED_FANS, EXTERNAL_PC | Set a fan's speed | `SPEED` 0.0 to 1.0, default 0 |
| PART_COOLING | Set the part fan's speed | `SPEED` 0.0 to 1.0, or 1.1 to 100 percent |
| RESET_FANS | Stop the four fans above | none |
| CHAMBER | Set the chamber heater target | `TEMP` in °C, default 0 |
| LED_ON, LED_DIM, LED_OFF | Set the LEDs to full, dim or off | none |
| DUMP_FAN | Print the part fan's status | none |
| MOTION_SENSOR, SWITCH_SENSOR | Enable or disable a filament sensor | `ENABLE` 0 or 1, default 1 |
| RELEASE_Z | Run `M84 Z`, which disables all motors | none |
| RELEASE_XY | Disable the XY steppers | none |
| HARDWARE_CHECK | Report what each role found | none |

A bad value is reported on the console and never raises. The three named fans and the sensors
stay as they are; the part fan and the chamber heater turn off.
[docs/COMMANDS.md](docs/COMMANDS.md) has the details and every message.

## Optional hotend fan monitor

`optional/fan_tach_monitor.cfg` pauses the print and turns the hotend off when the hotend fan
stops. It needs a `[heater_fan]` with a `tachometer_pin`, `[pause_resume]` and a `PAUSE` macro.

Set `min_rpm` after you include it, because it ships at 0, which watches nothing. With the hotend
hot, read your fan's `rpm` and set about three quarters of it:

```ini
[include Klipper-Hardware-Controls/optional/fan_tach_monitor.cfg]

[gcode_macro HOTEND_FAN_CHECK]
variable_min_rpm: 6500
```

[docs/FAN_MONITOR.md](docs/FAN_MONITOR.md) says how to read the `rpm`, how the monitor works and
what each of its messages means.

## Troubleshooting

- **A command does nothing and prints nothing.** Its role is off or names a device that does not
  exist. Commands stay silent about this on purpose. Run `HARDWARE_CHECK`.
- **`Unknown command`.** The command's module is not included, or Klipper was not restarted.
- **`hotend_fan - heater_fan hotend_fan not found`.** You included the fan monitor, and the fan
  does not exist. Name your hotend fan in `hotend_fan`.

## Updating and rolling back

Add this to `moonraker.conf`. It follows tagged releases; use `channel: dev` to follow `main`.

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

Update only while the printer is idle, and keep your changes outside the checkout. To roll back,
check out the previous tag and restart. The [changelog](CHANGELOG.md) says what each tag changes.

## More

- [Commands and messages](docs/COMMANDS.md)
- [Hotend fan monitor](docs/FAN_MONITOR.md)
- [Public interface](docs/API.md)
- [Testing](docs/TESTING.md) and [style](docs/STYLE.md)
- [Contributing](CONTRIBUTING.md). Report a safety problem as described in
  [SECURITY.md](SECURITY.md).

## License

GPL-3.0.
