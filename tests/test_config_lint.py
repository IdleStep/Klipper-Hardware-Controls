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

    def test_a_misspelt_macro_option_is_reported(self):
        problems = self.problems(
            '[gcode_macro HELLO]\ndescripton: Say hello\ngcode:\n  M117 hi\n')
        self.assertEqual(problems, [
            '[gcode_macro HELLO] has no description',
            '[gcode_macro HELLO] has options stock Klipper rejects: descripton'])

    def test_a_macro_with_the_options_klipper_reads_is_clean(self):
        self.assertEqual(self.problems(
            '[gcode_macro HELLO]\ndescription: Say hello\nrename_existing: HELLO_BASE\n'
            'variable_count: 0\ngcode:\n  M117 hi\n'), [])

    def test_other_section_types_are_not_checked(self):
        self.assertEqual(self.problems('[heater_bed]\ncontrol: mpc\n'), [])


if __name__ == '__main__':
    unittest.main()
