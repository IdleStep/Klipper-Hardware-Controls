# Contributing

Thank you for helping. Small, focused changes are easiest to review.

## Before you open a pull request

```sh
pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

The tests render the macros in a simulator and lint every config file. The real-firmware
tests (`tests/test_klippy.py`) run in CI against Klipper and Kalico; see the workflow for
how to run them locally.

- Follow [docs/STYLE.md](docs/STYLE.md). A change that follows it must not change what
  the printer does; if a change does alter behavior, say so in the description.
- A changed message changes its test and its README line in the same commit.
- Add an entry to the CHANGELOG under "Unreleased".
- Safety first: a command that gets bad input reports it and leaves the device as it is,
  or turns it off when off is the safe state. It does not raise.

## Versions

The version follows the public command API, as the CHANGELOG explains. Releases are
annotated tags named `vMAJOR.MINOR.PATCH`; Moonraker's `channel: stable` follows them.
