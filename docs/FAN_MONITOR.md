# Hotend fan monitor

`optional/fan_tach_monitor.cfg` pauses the print and turns the hotend off when the hotend fan
stops while the hotend is hot. The [README](../README.md) shows how to include it. This page
explains how it works and lists its messages.

## Requirements

- A `[heater_fan]` with a `tachometer_pin`, which means a 3-wire fan. The monitor watches
  `hotend_fan` unless the `hotend_fan` role of `_HARDWARE_VARS` names another.
- The package's `hardware_names.cfg`, which the monitor reads. The bundle includes it.
- `[respond]` for the messages, `[pause_resume]` and a `PAUSE` macro for the pause.

`hardware.cfg` does not include the monitor. Include it before the file that sets `min_rpm`.

## How it works

The monitor starts one second after Klipper starts and checks every `check_seconds` (3).

A check counts as a stop when the hotend's target and its temperature are both at or above the
fan's `heater_temp` and the fan's `rpm` is below `min_rpm`. After `max_consecutive_stops` (3)
stops in a row, `FAN_STOPPAGE_ROUTINE` runs. Any check that is not a stop resets the count.

The routine turns the hotend off first, then calls `PAUSE`. A `PAUSE` that fails still leaves
the hotend cold, and the monitor keeps running. If the print is already paused, the routine
turns the hotend off and does not call `PAUSE`.

The check is skipped when the fan does not exist, reports no `rpm`, or `min_rpm` is 0, so a
misconfigured fan cannot cause a false pause. The console says so once after each Klipper
start.

## Set min_rpm

The monitor ships with `min_rpm` at 0, which watches nothing. The right number depends on your
fan.

1. Heat the hotend above the fan's `heater_temp`.
2. Read the `rpm` of `heater_fan hotend_fan` in your web interface, or with
   `{printer["heater_fan hotend_fan"].rpm}` in a macro.
3. Choose a value well below it, such as three quarters, so that normal variation does not trip
   it while a stopped fan still does.

Set it in a file of your own that you include after the monitor:

```ini
[gcode_macro HOTEND_FAN_CHECK]
variable_min_rpm: 6500
```

`max_consecutive_stops` and `check_seconds` are variables of the same macro.

## Resuming after a stoppage

While the routine runs `PAUSE`, the hotend's old target is in
`printer["gcode_macro _HOTEND_FAN_STATE"].target`. It is 0 at any other time. A `PAUSE` macro that
saves the hotend target for `RESUME` can read it from there, and `RESUME` then heats the hotend
again. A `PAUSE` macro that does not read it saves a target of 0, and `RESUME` leaves the hotend
off.

To change what happens on a stoppage, override `FAN_STOPPAGE_ROUTINE` in your own file.

## Messages

Every message has the prefix ⚠️ unless the table says otherwise.

| Message | When | What to do |
|---|---|---|
| `Hotend fan is not monitored - no heater_fan {name} exists. Set hotend_fan in your hardware_names.cfg.` | The fan the role names is not in your configuration. | Set `hotend_fan` to the name after `heater_fan`. |
| `Hotend fan is not monitored - heater_fan {name} has no tachometer_pin.` | The fan exists but reports no `rpm`. | Add a `tachometer_pin` to the fan, or do not include the monitor. |
| `Hotend fan is not monitored - min_rpm is not set. Set it for HOTEND_FAN_CHECK as the README describes.` | `min_rpm` is 0. | Set `min_rpm` as described above. |
| `Hotend fan stopped ({n}/{max})` | A check counted a stop. `{max}` is `max_consecutive_stops`. | Check the fan. If `{n}` reaches `{max}`, the routine runs. |
| ❌ `Hotend fan stopped, pausing the print and turning the hotend off` | The routine runs and the print was not paused. | Fix the fan before you resume. A display shows `Hotend fan stopped`. |
| ❌ `Hotend fan stopped, turning the hotend off` | The routine runs and the print was already paused. | Fix the fan before you resume. |

Of the first three, only the one that applies appears, once after each Klipper start, however
many checks follow.

The idea comes from the fan tach monitor in Andrew Ellis's Print-Tuning-Guide. The file is
written for this package.
