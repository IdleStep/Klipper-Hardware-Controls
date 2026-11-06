"""klipper_test_kit works on its own: no Hardware Controls file, device or name is needed.

Run with: python -m unittest discover -s tests -v
"""
import ast
import pathlib
import tempfile
import unittest

import klipper_test_kit
from klipper_test_kit import Printer, State, wrap

KIT = pathlib.Path(klipper_test_kit.__file__).parent
# What the kit may import. A repository's own modules are not on the list.
IMPORTS = {'ast', 'configparser', 'copy', 'jinja2', 'pathlib', 'shlex'}

MACROS = '''[gcode_macro WARM]
variable_target: 60
gcode:
  SET_HEATER_TEMPERATURE HEATER=bed TARGET={target}
  SET_FAN_SPEED FAN=side SPEED={params.SPEED|default(0.5)}
  RESPOND MSG="warming"
  {action_respond_info("Warming to %d" % target)}
  SET_GCODE_VARIABLE MACRO=WARM VARIABLE=target VALUE=70
'''
STATE = {'heater_generic bed': {'target': 0.}, 'fan_generic side': {'speed': 0.}}


class Standalone(unittest.TestCase):
    def printer(self, **kwargs):
        printer = Printer(STATE, **kwargs)
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'macros.cfg'
            path.write_text(MACROS, encoding='utf-8')
            printer.load(path)
        return printer

    def test_a_macro_runs_against_the_state_it_was_given(self):
        printer = self.printer()
        printer.run('WARM', SPEED=0.8)
        self.assertEqual(printer.state['heater_generic bed'].target, 60)
        self.assertEqual(printer.state['fan_generic side'].speed, 0.8)
        self.assertEqual(printer.messages, ['Warming to 60'])
        self.assertEqual(printer.state['gcode_macro WARM'].target, 70)

    def test_the_state_is_copied_not_kept(self):
        printer = self.printer()
        printer.run('WARM')
        self.assertEqual(STATE['heater_generic bed']['target'], 0.)
        self.assertNotIsInstance(STATE['heater_generic bed'], State)

    def test_a_printer_without_a_state_starts_empty(self):
        self.assertEqual(Printer().state, {})

    def test_the_idle_timeout_starts_at_klippers_default_unless_given(self):
        self.assertEqual(Printer().idle_timeout, 600.)
        self.assertEqual(Printer(idle_timeout=4800.).idle_timeout, 4800.)
        printer = Printer()
        printer.execute('SET_IDLE_TIMEOUT TIMEOUT=900')
        self.assertEqual(printer.idle_timeout, 900.)

    def test_an_unknown_command_is_recorded_and_ignored(self):
        printer = Printer()
        printer.execute('G28 X')
        self.assertEqual(printer.commands, ['G28 X'])

    def test_a_subclass_can_give_a_command_an_effect(self):
        class Homing(Printer):
            def handle(self, name, args, tokens):
                if name == 'G28':
                    self.state['toolhead'] = wrap({'homed_axes': ''.join(tokens[1:]).lower()})

        printer = Homing()
        printer.execute('G28 X Y')
        self.assertEqual(printer.state['toolhead'].homed_axes, 'xy')

    def test_a_command_with_no_effect_here_is_passed_to_handle(self):
        seen = []

        class Spy(Printer):
            def handle(self, name, args, tokens):
                seen.append(name)

        printer = Spy()
        for line in ['G28', 'SET_GCODE_OFFSET Z_ADJUST=0.1', 'SET_IDLE_TIMEOUT TIMEOUT=900']:
            printer.execute(line)
        # The state has no gcode_move, so SET_GCODE_OFFSET has no effect; SET_IDLE_TIMEOUT has one.
        self.assertEqual(seen, ['G28', 'SET_GCODE_OFFSET'])

    def test_set_gcode_offset_needs_a_gcode_move_in_the_state(self):
        bare = Printer()
        bare.execute('SET_GCODE_OFFSET Z_ADJUST=0.1')
        self.assertNotIn('gcode_move', bare.state)
        moving = Printer({'gcode_move': {'homing_origin': {'z': 0.}}})
        moving.execute('SET_GCODE_OFFSET Z_ADJUST=0.1')
        self.assertAlmostEqual(moving.state['gcode_move'].homing_origin.z, 0.1)


class StaysGeneral(unittest.TestCase):
    """What lets the package move into a repository of its own."""

    def sources(self):
        return sorted(KIT.glob('*.py'))

    def test_it_imports_only_the_standard_library_and_jinja(self):
        for source in self.sources():
            tree = ast.parse(source.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and not node.level:
                    modules = [node.module]
                else:
                    continue
                for module in modules:
                    with self.subTest(file=source.name, module=module):
                        self.assertIn(module.split('.')[0], IMPORTS)

    def test_it_names_no_repository_or_package(self):
        for source in self.sources():
            text = source.read_text(encoding='utf-8').lower()
            for word in ('hardware', 'hw_root', 'cooldown', 'klipper-configs', 'chamber'):
                with self.subTest(file=source.name, word=word):
                    self.assertNotIn(word, text)


if __name__ == '__main__':
    unittest.main()
