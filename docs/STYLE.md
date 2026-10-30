# Style

One set of conventions for Klipper-Hardware-Controls and Klipper-Chamber-Cooldown. A change
that follows them must not change what the printer does.

## Files

- A macro file reads top to bottom: header comment, state macros (`_X_VARS`, tables),
  public commands in the order a user meets them, private `_` helpers in the order they
  are called, then `delayed_gcode` sections.
- A `[gcode_macro]` section lists `rename_existing`, `description`, `variable_*`, `gcode`.
  Every public macro has a `description` (imperative, sentence case, no final period).
- Includes: dependency order where one file needs another, otherwise alphabetical.
  `macros_<printer>.cfg` starts with `common.cfg`. Tables with no meaning in their order
  (materials, profiles, `global_vars`) are alphabetical, with `DEFAULT` first.
- Inside a macro: parameters, derived values (`{% set %}`), validation, actions,
  reporting. Only `{% set %}` lines may move. A command that runs never moves, because
  the order in which commands reach the printer is behavior.

## Formatting

- LF line endings, no tabs, no trailing whitespace, a final newline.
- Two spaces in `gcode:` bodies and Jinja blocks. Tags are indented with the code they
  wrap. A wrapped expression continues four spaces further in.
- 100 columns for Jinja tags, comments, Python and prose in code blocks. A single gcode
  command line (including `RESPOND`) cannot wrap and is exempt; name a value first to
  keep it short. Data tables are exempt.
- One blank line between sections and macros, at most one inside a body, none directly
  after `gcode:`. Python follows PEP 8.
- `key: value` with one space. Jinja filters without spaces: `value|float`.
  `RESPOND PREFIX="..."` always quoted.
- Third-party files kept close to upstream so they can be compared and updated are exempt
  from this page and from the lint. Change them only to make them work here.

## Names

- Local Jinja variables are lower snake_case. `temp` for a temperature (`chamber_temp`),
  `target` for a heater target (`bed_target`), `<role>_speed` for a fan speed
  (`bed_fans_speed`). Order is `<device>_<quantity>`.
- `name` is the short device name (`exhaust_fan`). A local that holds the full printer
  object (`"fan_generic exhaust_fan"`) ends in `_object`.
- `hw` is `_HARDWARE_VARS`, `cv` is `_COOLDOWN_VARS`. Internal macros and variables
  start with `_`.
- Single letters are for loop indices only. In tests: `printer`, `command`, `message`.

## Moonraker

An `[update_manager]` section is named after the repository it updates, exactly:
`[update_manager Klipper-Hardware-Controls]`, `[update_manager Klipper-Chamber-Cooldown]`.
A printer does not use another name for it (`hardware_controls`).

## Comments

Comments say why, never what. They sit on the line above the code, as sentences. Do not
leave comments about things that were removed, and do not keep commented-out code. A data
table may carry its notes in a trailing column.

## Console messages

- Start with a capital letter. No `key: value` dumps. No final period on a short
  phrase; a period when there are two sentences.
- Plain spaced hyphen, never an em dash. `°C` stays against the number; `mm`, `s` and
  `min` have a space (`15 mm`, `5 s`).
- Names and values are not quoted. Free text is quoted with single quotes, never with
  an escaped double quote. A `;` never appears in a message: Kalico cuts the line there.
- Prefix: 📃 note, ⚠️ warning, ❌ error or refusal. Other emoji mark events (🔥 heating,
  🧊 cooldown).

## Tests

- Test classes follow the order of the code they cover. Test names read as sentences.
- Helpers sit at the top of the class. Repeated state keys are constants.
- Changing a message changes its test and its README line in the same commit.
