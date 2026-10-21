"""Hardware Controls under real Klipper; see klippy_batch.py for setup."""
import pathlib
import unittest

from klippy_batch import run_script_files
from klipper_sim import HW_ROOT

SCRIPTS = pathlib.Path(__file__).resolve().parent / 'klippy'


class RealKlipper(unittest.TestCase):
    def test_scripts(self):
        run_script_files(self, SCRIPTS, (SCRIPTS / 'printer.cfg').read_text(encoding='utf-8'),
                         {'Klipper-Hardware-Controls': HW_ROOT})


if __name__ == '__main__':
    unittest.main()
