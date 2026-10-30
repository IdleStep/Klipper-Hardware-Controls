"""Hardware Controls under real Klipper; see klippy_batch.py for setup.

Every run uses the test printer in tests/klippy/printer.cfg plus two files that only these runs
include: record_pause.cfg and record_respond.cfg, which record what PAUSE and RESPOND were asked.
The scripts directly in tests/klippy run on the test printer as it is. Each folder in
tests/klippy/cases runs on the same printer with the two lines that include the package and the
names file replaced by that folder's includes.txt.
"""
import pathlib
import unittest

from klippy_batch import run_script_files, skip_unless_configured
from klipper_sim import HW_ROOT

SCRIPTS = pathlib.Path(__file__).resolve().parent / 'klippy'
PRINTER = (SCRIPTS / 'printer.cfg').read_text(encoding='utf-8')
PACKAGE_INCLUDES = ('[include Klipper-Hardware-Controls/hardware.cfg]\n'
                    '[include klippy-support/hardware_names.cfg]\n')
RECORDERS = ('[include klippy-support/record_pause.cfg]\n'
             '[include klippy-support/record_respond.cfg]\n')
LINKS = {'Klipper-Hardware-Controls': HW_ROOT}


class RealKlipper(unittest.TestCase):
    def test_scripts(self):
        run_script_files(self, SCRIPTS, PRINTER + RECORDERS, LINKS)

    def test_the_include_order_and_the_names_decide_which_role_wins(self):
        skip_unless_configured(self)
        self.assertIn(PACKAGE_INCLUDES, PRINTER)
        for case in sorted(path for path in (SCRIPTS / 'cases').iterdir() if path.is_dir()):
            with self.subTest(case=case.name):
                includes = (case / 'includes.txt').read_text(encoding='utf-8')
                run_script_files(self, case, PRINTER.replace(PACKAGE_INCLUDES, includes) + RECORDERS,
                                 LINKS)


if __name__ == '__main__':
    unittest.main()
