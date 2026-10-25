import pathlib
import tempfile
import unittest

from config_lint import lint, lint_file
from klipper_sim import HW_ROOT


class ConfigLint(unittest.TestCase):
    def test_config_files_are_clean(self):
        self.assertEqual(lint(HW_ROOT), {})

    def problems(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'test.cfg'
            path.write_bytes(text.encode('utf-8'))
            return lint_file(path)

    def test_a_delayed_gcode_with_a_description_is_reported(self):
        problems = self.problems(
            '[delayed_gcode WAKE]\ndescription: Wake up\ninitial_duration: 1\ngcode:\n  M117 hi\n')
        self.assertEqual(problems,
                         ['[delayed_gcode WAKE] has options stock Klipper rejects: description'])

    def test_a_delayed_gcode_with_the_options_klipper_reads_is_clean(self):
        self.assertEqual(
            self.problems('[delayed_gcode WAKE]\ninitial_duration: 1\ngcode:\n  M117 hi\n'), [])


if __name__ == '__main__':
    unittest.main()
