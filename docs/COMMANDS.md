# Commands

What each command does with its parameters, and every message it can print. The
[README](../README.md) has the short table. [API.md](API.md) lists the names this package
promises to keep.

A command whose role is off, or whose role names a device that does not exist, does nothing and
says nothing. Run [`HARDWARE_CHECK`](#hardware_check) to see which. A bad value is reported on
the console and never raised, so it cannot abort the macro or the print that sent it.

Each section below says whether its role takes several devices or one. A role that takes several
devices is a name, a comma-separated string or a list, and the command acts on every device that
exists. A role that takes one device is a single name, and a comma in it is not a separator. The
[README](../README.md#name-your-devices) lists both groups.

## Fans

`EXHAUST_FAN`, `BED_FANS` and `EXTERNAL_PC` set the speed of the fans named by the role of the
same name. These roles take several devices, and the command sets every fan that exists to the
same speed. `SPEED` is `0.0` to `1.0` and defaults to 0, which stops the fans. Any other value,
text included, leaves the fans as they are, and is reported once, not once per fan.

`PART_COOLING` sets the part fan named by `part_fan`, which takes one device. `SPEED` is `0.0` to
`1.0`, or `1.1` to `100` as a percentage, and defaults to 0. Any other value turns the fan off. A
`[fan]` gets `M106`; a `[fan_generic]` gets `SET_FAN_SPEED`. The command adds no minimum speed.
The fan's own `min_power` or `off_below` decides what a small speed does, and Klipper and Kalico
do not treat them alike.

`RESET_FANS` stops the part fan, every external fan, every bed fan and every exhaust fan.

`DUMP_FAN` prints every status value of the part fan to the console.

## Chamber

`CHAMBER` sets the target of the heaters named by `chamber_heater`, which takes several devices.
Every heater that exists gets the same target. `TEMP` is in °C and defaults to 0, which turns
the heaters off. Text or a negative value turns them off. Klipper itself refuses a target above
a heater's `max_temp`.

## LEDs

`LED_ON` sets every configured neopixel and output pin to full brightness. `LED_OFF` sets
them to 0. `LED_DIM` sets the neopixels to `neopixel_level` and the pins to `pin_level`, both
variables of `[gcode_macro LED_DIM]` that default to 0.33. Override them in a file included after
the package:

```ini
[gcode_macro LED_DIM]
variable_neopixel_level: 0.2
variable_pin_level: 0.5
```

An output pin without `pwm` takes only 0 and 1. `LED_DIM` leaves such a pin as it is.

`led_neopixels` and `led_pins` take several devices: `"daystick, nightstick"` and
`["daystick", "nightstick"]` name the same two pins.

## Filament sensors

`MOTION_SENSOR` and `SWITCH_SENSOR` enable or disable the sensor named by `motion_sensor` or
`switch_sensor`. Each of these roles takes one device. `ENABLE` is `0` or `1` and defaults to 1. Any other value, text included, leaves
the sensor as it is, so a typo cannot switch off runout detection.

`sensors.cfg` also defines the delayed gcode `ENABLE_MOTION_SENSOR`. It runs
`MOTION_SENSOR ENABLE=1` and has no `initial_duration`, so it does nothing until the printer
workflow schedules it, for example with
`UPDATE_DELAYED_GCODE ID=ENABLE_MOTION_SENSOR DURATION=60`. Including the module does not change
a sensor's state.

The two macros also carry the variables `fmotion_enabled` and `fswitch_enabled`. This package
does not read them. A `PAUSE` macro can save each sensor's state in them and a `RESUME` macro can
restore it.

## Steppers

`RELEASE_Z` runs `M84 Z`. Klipper and Kalico disable all motors for it, not only Z.

`RELEASE_XY` disables each stepper in `release_xy_steppers` on its own, and skips a name that
is not in your configuration. The role takes several devices. Nothing here runs by itself.
Disabling a stepper does not clear homing, so rehome after you move a disabled axis by hand.

## HARDWARE_CHECK

`HARDWARE_CHECK` changes nothing and nothing calls it. For every role of `_HARDWARE_VARS` it
prints one line per name: the device it found, that the role is off, or that the name matches
nothing. A role that takes several devices is checked name by name. A role that takes one device
is checked as one name, so `"a, b"` in it is reported as a name that matches nothing. It also
flags a name written with its section type and a key that is not a role. The last line gives the
count of problems. Run it after you edit your `_HARDWARE_VARS` section.

The `hotend_fan` role matters only to the [hotend fan monitor](FAN_MONITOR.md). Without the
monitor, `HARDWARE_CHECK` says the role is not used and does not look for the fan.

## Messages

Each message starts with the prefix shown. Names and values in `{braces}` are filled in.

| Prefix | Message | Command | Meaning |
|---|---|---|---|
| ❌ | `Fan speed must be between 0.0 and 1.0 (got {value})` | EXHAUST_FAN, BED_FANS, EXTERNAL_PC | `SPEED` is out of range or not a number. The fan is unchanged. |
| ⚠️ | `Invalid PART_COOLING value {value}, set to 0` | PART_COOLING | `SPEED` is out of range or not a number. The fan is off. |
| ⚠️ | `Invalid CHAMBER value {value}, set to 0` | CHAMBER | `TEMP` is negative or not a number. The heater is off. |
| ❌ | `MOTION_SENSOR ENABLE must be 0 or 1 (got {value})` | MOTION_SENSOR | The sensor is unchanged. |
| ❌ | `SWITCH_SENSOR ENABLE must be 0 or 1 (got {value})` | SWITCH_SENSOR | The sensor is unchanged. |
| ⚠️ | `LED_DIM leaves {name} unchanged - the output pin has no pwm` | LED_DIM | Add `pwm: True` to the pin, or ignore it. |
| 📃 | `{role} - off` | HARDWARE_CHECK | The role is empty. |
| 📃 | `hotend_fan - not used, the fan monitor is not included` | HARDWARE_CHECK | `optional/fan_tach_monitor.cfg` is not included, so the role is not checked. |
| 📃 | `{role} - {object} found` | HARDWARE_CHECK | The device exists. `{object}` is its section name, such as `fan_generic exhaust_fan`, or `stepper_x` for a stepper. |
| ⚠️ | `{role} - {object} not found` | HARDWARE_CHECK | No such device. Check the spelling and the section in your printer configuration. |
| ⚠️ | `{role} - {name} starts with the section type, give only the name after it` | HARDWARE_CHECK | Write `exhaust_fan`, not `fan_generic exhaust_fan`. |
| ⚠️ | `{key} is not a role - misspelt or removed` | HARDWARE_CHECK | A variable in your `_HARDWARE_VARS` is not a role of this package. |
| ⚠️ | `Hardware check found {n} to fix` | HARDWARE_CHECK | The last line when there is a problem. |
| 📃 | `Hardware check found nothing to fix` | HARDWARE_CHECK | The last line when everything matches. |

The messages of the hotend fan monitor are in [FAN_MONITOR.md](FAN_MONITOR.md#messages).
