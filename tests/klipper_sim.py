"""Hardware Controls' simulated printer, built on klipper_test_kit.

It renders the real gcode_macro / delayed_gcode templates of this package and executes the
commands they emit against an in-memory printer state. No printer is contacted. Other
repositories import this module from their Hardware-Controls checkout, so keep the names listed
in docs/API.md stable. The simulator itself is in klipper_test_kit; this module adds what is
particular to this package: its module list, its test printer's devices and names.

HARDWARE_CONTROLS_ROOT, when set, loads the package configs from another
checkout (a repository can use it to test against its oldest supported release).
It is not HARDWARE_CONTROLS_PATH: a repository that reuses this module reads that to
find this checkout, which is beside it by default. This module does not.
"""
import os
import pathlib

from klipper_test_kit import Printer as KitPrinter
from klipper_test_kit import State, wrap  # noqa: F401  (re-exported: docs/API.md lists them here)

HW_ROOT = pathlib.Path(
    os.environ.get('HARDWARE_CONTROLS_ROOT') or pathlib.Path(__file__).parents[1]).resolve()
HARDWARE_MODULES = [
    'hardware_names', 'fans', 'chamber', 'leds', 'dump_fan', 'sensors', 'release_steppers',
    'hardware_check']


def module_path(name):
    """The config file of a module in the checkout under test."""
    return HW_ROOT / (name + '.cfg')


# The test printers' own hardware_names.cfg, included after the modules like a printer's.
# It lives beside the real-firmware scripts, which include the same file.
HARDWARE_NAMES = pathlib.Path(__file__).resolve().parent / 'klippy' / 'hardware_names.cfg'
DEFAULT_IDLE_TIMEOUT = 4800.


def default_state():
    """A printer with a heated chamber, a bed, a part fan, a hotend fan, generic fans and sensors.

    These are the devices of tests/klippy/printer.cfg. The hotend fan has no tachometer.
    """
    return wrap({
        'idle_timeout': {'state': 'Idle'},
        'heater_generic chamber': {'target': 55., 'temperature': 55.},
        'heater_bed': {'target': 0., 'temperature': 80.},
        'fan': {'speed': 0.},
        'heater_fan hotend_fan': {'speed': 0., 'rpm': None},
        'fan_generic exhaust_fan': {'speed': 0.},
        'fan_generic bed_fans': {'speed': 0.},
        'fan_generic external_pc': {'speed': 0.},
        'filament_motion_sensor motion_sensor': {'enabled': False},
        'filament_switch_sensor switch_sensor': {'enabled': False},
        'pause_resume': {'is_paused': False},
        'configfile': {'settings': {
            'heater_fan hotend_fan': {'heater_temp': 50.},
            'stepper_x': {},
            'stepper_y': {},
            'idle_timeout': {'timeout': DEFAULT_IDLE_TIMEOUT},
        }},
    })


class Printer(KitPrinter):
    """A printer with this package's modules loaded, or without them with hardware=False.

    See klipper_test_kit.Printer for the attributes and methods.
    """

    def __init__(self, hardware=True):
        super().__init__(default_state(), idle_timeout=DEFAULT_IDLE_TIMEOUT)
        if hardware:
            for name in HARDWARE_MODULES:
                self.load(module_path(name))
            self.load(HARDWARE_NAMES)
