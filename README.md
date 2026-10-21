# Klipper Hardware Controls

Reusable hardware commands for Klipper configurations and chamber cooldown.
This package depends on standard Klipper macros and `[respond]`, not on
Klipper-Configs or the cooldown repository. Public command API: version 1.

## Install

Clone into `~/printer_data/config/Klipper-Hardware-Controls`, then include once:

```ini
[include Klipper-Hardware-Controls/hardware.cfg]
[include hardware-local.cfg]
```

Alternatively include `settings.cfg` and only needed modules: `fans.cfg`,
`chamber.cfg`, `leds.cfg`, `sensors.cfg`, `dump_fan.cfg`, `release_steppers.cfg`.
Cooldown requires settings, fans and chamber. Never load both bundle and individual
copies. Replace old helper includes before loading this package.

Define physical devices, pins, sensor types, heater verification and power limits
in printer configuration. Copy the local settings example outside this checkout
and load it after defaults. Object names must be valid Klipper configuration names.
Generic fan settings take names without the `fan_generic ` prefix; chamber_sensor,
bed_heater and part_fan take full object names. Empty names disable optional roles.

## Commands

| Command | Parameters / behavior |
|---|---|
| EXHAUST_FAN, BED_FANS, EXTERNAL_PC | SPEED=0.0 through 1.0 |
| PART_COOLING | SPEED=0.0 through 1.0, or 1.1 through 100 percent |
| RESET_FANS | Stops all configured controlled fan roles |
| CHAMBER | TEMP=target in °C |
| LED_ON, LED_OFF, LED_DIM | Configured neopixel and output-pin groups |
| DUMP_FAN | Configured part fan status |
| MOTION_SENSOR, SWITCH_SENSOR | ENABLE=0 or 1 (default 1) |
| RELEASE_Z | Preserves legacy M84 Z; stock Klipper disables ALL motors |
| RELEASE_XY | Disables configured XY steppers individually |

Missing optional devices are skipped. Generic fan speeds outside 0..1, or not a
number, error before issuing a device command. PART_COOLING preserves legacy
percent/fraction handling: any other value (for example 255, 1.05 or text) turns
the fan off and reports "invalid PART_COOLING value" instead of aborting a print.
Speeds below the fan's `min_power` (or `off_below` when `min_power` is unset) turn
it off, as before.
LED dim defaults preserve 0.3098 for neopixels and 0.33 for output pins.
Stepper release never runs automatically. Individual-stepper disable does not
invalidate homing information; rehome after manually moving disabled axes.

## Sensor scheduling

`sensors.cfg` includes an inert callback, with no initial_duration:

```ini
[delayed_gcode ENABLE_MOTION_SENSOR]
gcode:
  MOTION_SENSOR ENABLE=1
```

Existing callers continue scheduling it with:

```gcode
UPDATE_DELAYED_GCODE ID=ENABLE_MOTION_SENSOR DURATION=60
```

The printer workflow owns when to schedule it. Including the module does not
change sensor state. Klipper-Configs owns startup disable_sensors in its common
macro file (initial_duration 0.1; MOTION_SENSOR ENABLE=0).

## Optional monitoring

`optional/fan_tach_monitor.cfg` preserves the existing Andrew Ellis/alch3my monitor.
Include it explicitly only on printers with `heater_fan hotend_fan` and a tachometer.
It starts after one second, checks every three seconds, and can PAUSE and turn
off the hotend using existing policy. Default minimum is 8000 RPM. The check is
skipped when `hotend_fan` is missing or reports no RPM (no `tachometer_pin`), so a
misconfigured fan cannot trigger false pauses. It is excluded
from hardware.cfg, and retains its original device names and policy for this
migration. Turbo's existing activation must be replaced with this optional include.

## Updates and rollback

Use examples/moonraker.conf. Keep overrides outside the checkout. Preserve public
API compatibility within version 1; record exact tested hardware and consumer
revisions for each printer. Restart/update only while inactive. Restore old
includes and affected integrations together if validation fails. Other printers
must install this dependency before updating to the cleaned Klipper-Configs.

Run tests with `pip install -r requirements-test.txt` followed by
`python -m unittest discover -s tests -v`. Tests simulate commands without hardware.
GPL-3.0 applies; optional monitoring retains upstream attribution.
