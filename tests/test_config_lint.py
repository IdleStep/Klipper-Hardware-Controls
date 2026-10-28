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

    def test_a_macro_section_that_only_sets_variables_needs_no_description(self):
        self.assertEqual(self.problems('[gcode_macro HELLO]\nvariable_count: 1\n'), [])

    def test_an_unquoted_respond_prefix_is_reported(self):
        for prefix in ['PREFIX=x', 'PREFIX=', "PREFIX='x'"]:
            with self.subTest(prefix=prefix):
                problems = self.problems(
                    '[gcode_macro _HELLO]\ngcode:\n  RESPOND %s MSG="hi"\n' % prefix)
                self.assertEqual(problems, ['line 3: RESPOND PREFIX must be double-quoted'])

    def test_a_quoted_respond_prefix_is_clean(self):
        for prefix in ['PREFIX="x"', 'PREFIX=""']:
            with self.subTest(prefix=prefix):
                self.assertEqual(self.problems(
                    '[gcode_macro _HELLO]\ngcode:\n  RESPOND %s MSG="hi"\n' % prefix), [])

    def test_an_option_not_written_key_colon_space_value_is_reported(self):
        for option in ['pin:PA1', 'pin :PA1', 'pin:  PA1', 'pin : PA1']:
            with self.subTest(option=option):
                self.assertEqual(self.problems('[fan]\n%s\n' % option),
                                 ['line 2: write the option as `key: value` with one space'])

    def test_options_written_key_colon_space_value_are_clean(self):
        self.assertEqual(self.problems('[fan]\npin: PA1\nkick_start_time:\n# pin:PA2\n'), [])

    def test_a_line_past_100_columns_is_reported_unless_it_is_one_command(self):
        text = '[gcode_macro _HELLO]\ngcode:\n  %s\n'
        long = 'x' * 100
        for line, expected in [
                ('# ' + long, ['line 3: 104 columns, the limit is 100']),
                ('{%% set a = "%s" %%}' % long, ['line 3: 118 columns, the limit is 100']),
                ('RESPOND PREFIX="📃" MSG="%s"' % long, []),
                ('{action_raise_error("%s")}' % long, []),
                ('_HELPER VALUE=%s' % long, []),
                ('x' * 98, [])]:
            with self.subTest(line=line[:20]):
                self.assertEqual(self.problems(text % line), expected)

    def test_the_column_limit_can_be_turned_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / 'test.cfg'
            path.write_bytes(('# %s\n' % ('x' * 120)).encode('utf-8'))
            self.assertEqual(lint_file(path, max_columns=None), [])

    def test_other_section_types_are_not_checked(self):
        self.assertEqual(self.problems('[heater_bed]\ncontrol: mpc\n'), [])


if __name__ == '__main__':
    unittest.main()
