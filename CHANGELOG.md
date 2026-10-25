# Changelog

Versions follow the public command API: the major version changes only when a
command, parameter or `_HARDWARE_VARS` name changes incompatibly.

## 1.2.0

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

## 1.1.0

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

## 1.0.0

Initial extraction from Klipper-Configs.
