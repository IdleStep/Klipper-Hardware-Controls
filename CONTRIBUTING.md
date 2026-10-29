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
- The Klipper and Kalico revisions in `.github/workflows/templates.yml` are also pinned in
  the workflows of the repositories that reuse these tests. When you move them, change all
  of them together.
- Safety first: a command that gets bad input reports it and leaves the device as it is,
  or turns it off when off is the safe state. It does not raise.

## Versions

The version follows the public interface listed in [docs/API.md](docs/API.md), as the
CHANGELOG explains. Versions are annotated tags named `vMAJOR.MINOR.PATCH`; Moonraker's
`channel: stable` follows them.

To release: in a pull request, rename `[Unreleased]` in the CHANGELOG to the version and
date, add the compare link at the bottom and a fresh `[Unreleased]` heading above it. After
it is merged, tag the merge commit.
