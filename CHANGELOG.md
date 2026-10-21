# Changelog

Versions follow the public command API: the major version changes only when a
command, parameter or `_HARDWARE_VARS` name changes incompatibly.

## 1.1.0

### Fixed
- PART_COOLING reports `invalid PART_COOLING value` again (lost in the
  extraction) when it turns the fan off for an out-of-range or non-numeric value.
- EXHAUST_FAN, BED_FANS and EXTERNAL_PC reject non-numeric speeds instead of
  silently stopping the fan.
- The optional fan tachometer monitor no longer errors every 3 s without
  `hotend_fan`, or pauses prints when the fan has no tachometer.

### Changed
- Public macros have descriptions in Mainsail and Fluidd.
- `settings.cfg` and `examples/hardware-local.cfg` document every role.
- Moonraker example follows tagged releases.
- Tests: shared simulator (`tests/klipper_sim.py`), config lint, and real Klipper
  and Kalico batch runs in CI.

## 1.0.0

Initial extraction from Klipper-Configs.
