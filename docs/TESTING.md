# Testing

For contributors. A user does not need this page.

```sh
pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Three layers check the package. The first two run anywhere. The third needs a Klipper or
Kalico checkout and runs in CI.

| Layer | File | What it checks |
|---|---|---|
| Simulator | `tests/test_templates.py`, `tests/klipper_sim.py` | The macros render and emit the commands and messages this package promises. |
| Lint | `tests/config_lint.py`, `tests/test_config_lint.py` | Every `.cfg` file follows [STYLE.md](STYLE.md). |
| Real firmware | `tests/test_klippy.py`, `tests/klippy/` | The package loads in real Klipper and Kalico and behaves as the simulator says. |

`tests/test_api_doc.py` fails when a command, role or variable is missing from
[API.md](API.md), or when a name that file lists does not exist.

## Simulator

`tests/klipper_sim.py` renders the macros with Klipper's Jinja delimiters and runs the commands
they emit against an in-memory printer. Messages are asserted there, so a changed message changes
its test and its README line in the same commit.

The simulator includes `tests/klippy/hardware_names.cfg`, the test printers' own names file,
after the package, as a printer does. [API.md](API.md#for-other-repositories) lists the names
other repositories may import.

| Variable | Read by | Meaning |
|---|---|---|
| `HARDWARE_CONTROLS_ROOT` | the simulator | Load the package configs from another checkout, for example an older release. |
| `HARDWARE_CONTROLS_PATH` | a repository that reuses the simulator | Where to find this checkout. By default it is beside that repository. |

CI runs the simulator on Jinja 3.1, which Kalico uses, and on Jinja 2.11.3, which Klipper uses.

## Lint

`tests/config_lint.py` checks every `.cfg` for:

- parse errors and broken includes
- CRLF line endings, tabs, trailing whitespace and a missing final newline
- lines past 100 columns, except a single gcode command
- an option not written `key: value` with one space
- an unquoted `RESPOND PREFIX` or a malformed `RESPOND` message
- a macro without a description
- a `gcode_macro` or `delayed_gcode` option that stock Klipper does not read

## Real firmware

`tests/test_klippy.py` loads the package in Klipper or Kalico without hardware and runs the
scripts in `tests/klippy/*.gcode`. They assert fan speeds, heater targets, output pin and LED
values, sensor state and the pause state after the commands.

Each folder in `tests/klippy/cases` runs scripts with a different include order or a mistake in
the names. Its `includes.txt` replaces the two lines that include the package and the names
file.

The tests are skipped unless all three variables are set. `KLIPPY_REQUIRED=1` turns a skip into
an error.

| Variable | Meaning |
|---|---|
| `KLIPPER_DIR` | A Klipper or Kalico source checkout. |
| `KLIPPY_DICT` | The data dictionary from building the Linux process MCU. |
| `KLIPPY_PYTHON` | A Python with the firmware's `scripts/klippy-requirements.txt` installed. |

[`templates.yml`](../.github/workflows/templates.yml) shows how to build them and pins the
revisions it runs. [`firmware-canary.yml`](../.github/workflows/firmware-canary.yml) runs the same
tests every week on the newest Klipper and Kalico.

In batch mode a delayed gcode timer never fires and a fan's speed never reaches the status,
so the scripts check what the macros asked for. `tests/klippy/assert.cfg` records it.
