# Changelog

Versions follow the public command API: the major version changes only when a
command, parameter or `_HARDWARE_VARS` name changes incompatibly.

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
- Code, comments, tests and README tidied, with no behavior change.
- Tests: shared simulator (`tests/klipper_sim.py`), config lint, and real Klipper
  and Kalico batch runs in CI.

## 1.0.0

Initial extraction from Klipper-Configs.
