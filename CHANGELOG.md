# Changelog

Versions follow the public command API: the major version changes only when a
command, parameter or `_HARDWARE_VARS` name changes incompatibly.

## [Unreleased]

This is a major release. Before a printer updates, copy the roles it uses from the old
`settings.cfg` into its `hardware-local.cfg`. The old defaults were `chamber_heater`
`"chamber"`, `chamber_sensor` `"heater_generic chamber"`, `exhaust_fan` `"exhaust_fan"`,
`bed_fans` `"bed_fans"`, `external_pc` `"external_pc"`, `motion_sensor` `"motion_sensor"`,
`switch_sensor` `"switch_sensor"`, `led_neopixels` `["discostick", "th_leds"]`, `led_pins`
`["daystick"]`, `led_dim` `0.3098` and `led_pin_dim` `0.33`. A printer that includes the
fan tachometer monitor and sets `he_stop_count` or calls `CHECK_ALL_FANS` uses the new names
below.

### Added
- The `hotend_fan` role of `_HARDWARE_VARS` names the heater fan the optional tachometer
  monitor watches (default `hotend_fan`). When that fan does not exist or has no
  `tachometer_pin`, the console says so once; it used to skip every check without a word.

### Changed
- Breaking: `settings.cfg` is now `hardware_names.cfg`, which says what it holds, and it no
  longer holds the names of the author's printers. Every role that depends on a printer's
  own devices is off until its `hardware-local.cfg` names the device: `chamber_heater`,
  `chamber_sensor`, `exhaust_fan`, `bed_fans`, `external_pc`, `motion_sensor` and
  `switch_sensor` are `""`, `led_neopixels` and `led_pins` are `[]`, and `led_dim` and
  `led_pin_dim` are `0.3`. `bed_heater`, `part_fan` and
  `release_xy_steppers` keep their stock names. A printer's `hardware-local.cfg` starts
  as a copy of `hardware_names.cfg`; `examples/` is gone, and the Moonraker section is in
  the README.
- Breaking: the optional tachometer monitor's loop `CHECK_ALL_FANS` is now
  `HOTEND_FAN_MONITOR`, which says what it watches, and its stop counter `he_stop_count`
  is `stops` in the new `_HOTEND_FAN_STATE` macro. A local override of the
  `HOTEND_FAN_CHECK` settings no longer has to repeat the counter.
- SECURITY.md asks for a public issue instead of a private report.
- The changelog has dates and compare links, and Dependabot also watches the Python test
  requirement.
- README has a clone command, a CI badge and the firmware it is tested with.
  `docs/MIGRATION.md`, which was written for Klipper-Configs, is gone; its steps are in the
  1.0.0 entry.
- Tests: the config lint rejects any `gcode_macro` option that stock Klipper does not read
  (a misspelt `description` stops Klipper from loading), not only `delayed_gcode` ones. The
  real-firmware fan scripts assert the fan speeds the commands ask for, and a new script runs
  `FAN_STOPPAGE_ROUTINE` and asserts the pause and the hotend target. The simulator and the
  firmware runs include `tests/klippy/hardware-local.cfg` after the package, as a printer
  includes its own file. The simulator reads `settings.cfg` when the checkout under test is
  older than 2.0.0, which Cooldown's checks use for the oldest supported release.

## [1.2.0] - 2026-10-25

### Fixed
- MOTION_SENSOR and SWITCH_SENSOR report an `ENABLE` that is not 0 or 1 and leave
  the sensor as it is. Text used to count as 0 and silently disabled the sensor.
- EXHAUST_FAN, BED_FANS, EXTERNAL_PC and CHAMBER treat `nan` as invalid. It passed
  the range checks and reached `SET_FAN_SPEED` and `SET_HEATER_TEMPERATURE`.
- The optional fan tachometer monitor turns the hotend off when a fan stops while
  the print is already paused. It used to leave the hotend hot.

### Changed
- The optional fan tachometer monitor is rewritten for this package. It no longer
  contains code from the Print-Tuning-Guide, which declares no licence, so the
  GPL-3.0 notice now covers the whole repository. Commands, variable names and
  defaults are unchanged (8000 RPM, 3 stops, a check every 3 s); the console lines
  are new (`Hotend fan stopped (1/3)`), and the limits and the check interval are
  variables of `HOTEND_FAN_CHECK`: `min_rpm`, `max_consecutive_stops`,
  `check_seconds`.
- Messages for invalid input start with a prefix like the others: `❌` for a
  refusal (an invalid fan speed or sensor value), `⚠️` when the command still acts
  (`Invalid PART_COOLING value`, `Invalid CHAMBER value`). They are sent with
  `RESPOND`; the text is unchanged.
- Pull requests are checked with read-only token permissions, a firmware canary
  runs weekly against the newest Klipper and Kalico, and Dependabot proposes
  GitHub Action updates.
- CONTRIBUTING, SECURITY, issue and pull request templates and CODEOWNERS added.
- Tests: the config lint rejects `delayed_gcode` options that stock Klipper does not
  read (`description`); Kalico reads it, stock Klipper refuses to load the config.

## [1.1.0] - 2026-10-25

### Fixed
- PART_COOLING reports `Invalid PART_COOLING value` again (lost in the
  extraction) when it turns the fan off for an out-of-range or non-numeric value.
- EXHAUST_FAN, BED_FANS and EXTERNAL_PC reject non-numeric speeds instead of
  silently stopping the fan.
- An invalid EXHAUST_FAN, BED_FANS or EXTERNAL_PC speed is reported once as
  `Fan speed must be between 0.0 and 1.0` and leaves the fan unchanged. It used
  to raise, which Klipper and Kalico print as `Error evaluating ...` once per
  macro level and which aborted the calling macro or print.
- An invalid CHAMBER temperature (text or below 0) is reported as
  `Invalid CHAMBER value`; the heater is still turned off, as before.
- The optional fan tachometer monitor no longer errors every 3 s without
  `hotend_fan`, or pauses prints when the fan has no tachometer.

### Changed
- Public macros have descriptions in Mainsail and Fluidd.
- `settings.cfg` and `examples/hardware-local.cfg` document every role.
- Moonraker example follows tagged releases, and its section is named after the
  repository: `[update_manager Klipper-Hardware-Controls]`.
- Code, comments, tests and docs tidied, with no behavior change. Conventions are in
  `docs/STYLE.md`.
- The `Invalid PART_COOLING value` and `Invalid CHAMBER value` messages start with a
  capital, like the other messages.
- Tests: shared simulator (`tests/klipper_sim.py`), config lint, and real Klipper
  and Kalico batch runs in CI.

## [1.0.0] - 2026-10-25

Initial extraction from Klipper-Configs, where these commands were `macros/fans.cfg`,
`chamber.cfg`, `leds.cfg`, `sensors.cfg`, `dump_fan.cfg`, `release_steppers.cfg` and
`fan_tach_monitor.cfg`. Command names and behavior were kept.

To move a printer that used them: clone this repository, remove the old helper includes and
include `hardware.cfg` (or the modules you need) once, followed by your `hardware-local.cfg`.
A printer that used the old fan tachometer monitor includes `optional/fan_tach_monitor.cfg`
instead; it is no longer part of the bundle. Restart while idle and check that every
command still exists. To roll back, restore the old includes and the files that called the
helpers together, then restart while idle.

[Unreleased]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/tree/v1.0.0
