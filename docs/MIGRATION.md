# Migration from Klipper-Configs helpers

These commands previously lived in Klipper-Configs (`macros/fans.cfg`,
`chamber.cfg`, `leds.cfg`, `sensors.cfg`, `dump_fan.cfg`, `release_steppers.cfg`
and `fan_tach_monitor.cfg`). Command names and behavior were kept.

1. Clone this repository and add its Moonraker entry.
2. Remove the old helper includes, then include `hardware.cfg` (or the modules
   you need) once, followed by your `hardware-local.cfg`.
3. Printers that used the old fan tachometer monitor include
   `optional/fan_tach_monitor.cfg` instead; it is no longer part of the bundle.
4. Klipper-Configs keeps the startup `DISABLE_SENSORS` delayed gcode
   (`initial_duration: 0.1`, `MOTION_SENSOR ENABLE=0`); this package only provides
   the `ENABLE_MOTION_SENSOR` callback its print-start macros schedule.
5. Restart while idle and check that every command still exists.

Install this package on every printer before updating it to the Klipper-Configs
release that removed the helpers. To roll back, restore the old includes and the
Klipper-Configs files that called the helpers together, then restart while idle.
