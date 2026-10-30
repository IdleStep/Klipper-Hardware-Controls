# Changelog

Versions follow the public interface listed in [docs/API.md](docs/API.md).

- Major: a command, a parameter, a role of `_HARDWARE_VARS`, a variable a printer is told to
  set, a delayed gcode id or a listed test-tool name is renamed or removed.
- Minor: something is added, or a default or a lint rule changes in a way that can change
  what a printer does or what another repository's tests fail on. The entry says what to check.
- Patch: a fix that makes a command do what its documentation says.

## [Unreleased]

### Added
- `HARDWARE_CHECK` in the new `hardware_check.cfg`, which `hardware.cfg` includes. It reports
  for every role of `_HARDWARE_VARS` the device it finds, that it is off, a name that matches
  nothing, a name written with its section type, and an entry that is not a role. It changes
  nothing and nothing calls it. If you include the modules one by one, add `hardware_check.cfg`
  to use it.
- `_HOTEND_FAN_STATE.target`: the hotend target that `FAN_STOPPAGE_ROUTINE` turned off, while it
  runs `PAUSE`. Check: a `PAUSE` macro that saves the hotend target for `RESUME` should read it.
- Tests: the real-firmware runs cover the include order of the bundle, a module and your names
  file (`tests/klippy/cases`), `LED_DIM` on a pin without pwm, `HARDWARE_CHECK`, the sensor
  state and the order of the fan stoppage routine. `assert.cfg` records `SET_PIN` and `SET_LED`
  values. `templates.yml` runs the simulator on Jinja 2.11.3 as well as 3.1.6; its check is
  named `templates (Jinja 2.11.3)`.
- `docs/API.md` lists the public interface: commands and parameters, the roles and who reads
  them, the variables a printer may set, the delayed gcode ids and the names other
  repositories import from `tests/`. A test fails when a command, role or variable is missing
  from it.

### Changed
- Check: `min_rpm` of `HOTEND_FAN_CHECK` now ships as 0, which keeps the monitor from watching
  until a printer sets it; the console says so once. It was 8000, a number tuned to one fan.
  A printer that includes `optional/fan_tach_monitor.cfg` must set `variable_min_rpm` in a file
  included after the monitor. README: how to choose it.
- Check: `FAN_STOPPAGE_ROUTINE` turns the hotend off before it calls `PAUSE`, not after. A
  `PAUSE` macro that saves the hotend target now saves 0 unless it reads
  `_HOTEND_FAN_STATE.target`, so after a fan stoppage `RESUME` leaves the hotend off.
- `HOTEND_FAN_MONITOR` schedules its next run before it checks, so an error in the check or in
  `PAUSE` no longer ends the monitoring until the next restart.
- Check: `PART_COOLING` no longer turns off speeds below the fan's `min_power` or `off_below`.
  The firmware applies them: on Kalico a small speed now runs at about `min_power`, and on
  Klipper `off_below` still turns it off.
- `LED_DIM` leaves an output pin without `pwm` as it is and reports it. Klipper refuses any
  value but 0 and 1 for such a pin, and the error stopped the calling macro.
- Tests: `HARDWARE_LOCAL` in `klipper_sim.py` is now `HARDWARE_NAMES`, and `HARDWARE_MODULES`
  lists `hardware_check`. `default_state` has the `bed_fans` fan, the `hotend_fan` and
  `pause_resume`, and no longer reports an `off_below` for the part fan. The test printer has a
  second output pin, `plainstick`, without pwm.
- The version rule above covers settable variables, defaults, lint rules and the test-tool
  names, not only commands, parameters and role names.
- README: the role table says which command reads each role, `RESET_FANS` and its description
  say that it stops the part fan, and the text no longer names a repository that is not public.
- Tests: `klipper_sim.py` and the README say that a repository that reuses the simulator
  finds this checkout beside itself, or at `HARDWARE_CONTROLS_PATH`. That is not
  `HARDWARE_CONTROLS_ROOT`, which the simulator reads to load the package configs from another
  checkout.

### Removed
- Tests: `klipper_sim.module_path` no longer falls back to `settings.cfg`.

## [3.1.1] - 2026-10-28

### Changed
- Tests: the config lint also rejects an unquoted `RESPOND PREFIX`, an option not written
  `key: value` with one space, and a line past 100 columns (a single gcode command is exempt;
  `lint_file(path, max_columns=None)` turns the width check off). `docs/STYLE.md` says that
  vendored third-party files are exempt.

## [3.1.0] - 2026-10-27

### Changed
- `LED_DIM` dims to 0.33 by default, for the neopixels and the output pins alike (it was 0.3), so
  a printer sets the variables only to differ from that.

## [3.0.0] - 2026-10-27

### Added
- `LED_DIM` has the variables `neopixel_level` and `pin_level` (0.3 each), which a printer
  sets in its own LED file included after the package.

### Changed
- Tests: the config lint asks for a description only of a macro that has `gcode`, so a printer
  file can set the variables of a macro of the package, such as `LED_DIM`, without repeating it.

### Removed
- Breaking: `led_dim` and `led_pin_dim` are no longer roles of `_HARDWARE_VARS`, because
  `hardware_names.cfg` names devices and these are brightness levels. A printer that set
  either moves the value to the variables of `LED_DIM`.

## [2.0.0] - 2026-10-27

This is a major release. Before a printer updates, copy the roles it uses from the old
`settings.cfg` into its own `hardware_names.cfg`. The old defaults were `chamber_heater`
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
  own devices is off until its own `hardware_names.cfg` names the device: `chamber_heater`,
  `chamber_sensor`, `exhaust_fan`, `bed_fans`, `external_pc`, `motion_sensor` and
  `switch_sensor` are `""`, `led_neopixels` and `led_pins` are `[]`, and `led_dim` and
  `led_pin_dim` are `0.3`. `bed_heater`, `part_fan` and
  `release_xy_steppers` keep their stock names. A printer's own `hardware_names.cfg` starts
  as a copy of `hardware_names.cfg`, and the Moonraker section is in the README.
- Breaking: the optional tachometer monitor's loop `CHECK_ALL_FANS` is now
  `HOTEND_FAN_MONITOR`, which says what it watches, and its stop counter `he_stop_count`
  is `stops` in the new `_HOTEND_FAN_STATE` macro. A local override of the
  `HOTEND_FAN_CHECK` settings no longer has to repeat the counter.
- `docs/STYLE.md` says that an `[update_manager]` section is named after its repository.
- SECURITY.md asks for a public issue instead of a private report.
- The changelog has dates and compare links, and Dependabot also watches the Python test
  requirement.
- README has a clone command, a CI badge and the firmware it is tested with.
- Tests: the config lint rejects any `gcode_macro` option that stock Klipper does not read
  (a misspelt `description` stops Klipper from loading), not only `delayed_gcode` ones. The
  real-firmware fan scripts assert the fan speeds the commands ask for, and a new script runs
  `FAN_STOPPAGE_ROUTINE` and asserts the pause and the hotend target. The simulator and the
  firmware runs include `tests/klippy/hardware_names.cfg` after the package, as a printer
  includes its own file.

### Removed
- `examples/`.

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

First release: fan, chamber, LED, filament sensor and stepper commands, and the optional
fan tachometer monitor in `optional/fan_tach_monitor.cfg`, which is not part of the bundle.

[Unreleased]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v3.1.1...HEAD
[3.1.1]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v3.1.0...v3.1.1
[3.1.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/IdleStep/Klipper-Hardware-Controls/tree/v1.0.0
