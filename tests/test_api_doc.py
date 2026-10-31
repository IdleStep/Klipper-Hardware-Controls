"""docs/API.md names every public command, role and variable, and the names it lists exist.

Run with: python -m unittest discover -s tests -v
"""
import configparser
import importlib
import re
import unittest

from klipper_sim import HW_ROOT as HW

API = (HW / 'docs' / 'API.md').read_text(encoding='utf-8')
MODULES = ['fans', 'chamber', 'leds', 'dump_fan', 'sensors', 'release_steppers', 'hardware_check',
           'optional/fan_tach_monitor']
# Variables of private macros that docs/API.md tells a printer's macros to read.
READ = {'_HOTEND_FAN_STATE': ['target']}
# What docs/API.md lists for other repositories, by module.
TOOLS = {
    'klipper_sim': ['HW_ROOT', 'HARDWARE_MODULES', 'module_path', 'State', 'wrap',
                    'default_state', 'Printer'],
    'config_lint': ['lint_file', 'lint'],
    'klippy_batch': ['ENV', 'SUPPORT_DIR', 'skip_unless_configured', 'delayed_gcode_as_macro',
                     'run_script', 'error_lines', 'run_script_files'],
}


def sections(path):
    cfg = configparser.RawConfigParser(delimiters=(':',), strict=False, interpolation=None)
    cfg.read(path, encoding='utf-8')
    return cfg


class PublicInterface(unittest.TestCase):
    def mentioned(self, name):
        return re.search(r'`%s`|`[^`]*\b%s\b[^`]*`' % (name, name), API) is not None

    def test_every_public_command_and_delayed_id_is_listed(self):
        for module in MODULES:
            cfg = sections(HW / (module + '.cfg'))
            for section in cfg.sections():
                kind, _, name = section.partition(' ')
                if kind in ('gcode_macro', 'delayed_gcode') and not name.startswith('_'):
                    with self.subTest(section=section):
                        self.assertTrue(self.mentioned(name), '%s is not in docs/API.md' % name)

    def test_every_variable_of_a_public_macro_is_listed(self):
        for module in MODULES:
            cfg = sections(HW / (module + '.cfg'))
            for section in cfg.sections():
                kind, _, name = section.partition(' ')
                if kind != 'gcode_macro' or name.startswith('_'):
                    continue
                for option in cfg[section]:
                    if option.startswith('variable_'):
                        with self.subTest(macro=name, variable=option):
                            self.assertTrue(self.mentioned(option[len('variable_'):]),
                                            '%s.%s is not in docs/API.md' % (name, option))

    def test_the_variables_a_printer_may_read_exist_and_are_listed(self):
        cfg = sections(HW / 'optional/fan_tach_monitor.cfg')
        for macro, variables in READ.items():
            for variable in variables:
                with self.subTest(macro=macro, variable=variable):
                    self.assertIn('variable_' + variable, cfg['gcode_macro ' + macro])
                    self.assertTrue(self.mentioned(macro) and self.mentioned(variable))

    def test_every_role_is_listed(self):
        cfg = sections(HW / 'hardware_names.cfg')
        for option in cfg['gcode_macro _HARDWARE_VARS']:
            if option.startswith('variable_'):
                with self.subTest(role=option):
                    self.assertTrue(self.mentioned(option[len('variable_'):]),
                                    '%s is not in docs/API.md' % option)

    def test_the_listed_test_tool_names_exist(self):
        for module, names in TOOLS.items():
            tool = importlib.import_module(module)
            for name in names:
                with self.subTest(module=module, name=name):
                    self.assertTrue(hasattr(tool, name), '%s.%s does not exist' % (module, name))
                    self.assertTrue(self.mentioned(name), '%s is not in docs/API.md' % name)


class RoleGroups(unittest.TestCase):
    """Which roles take several devices is said in four places; they must agree.

    hardware_check.cfg is the reference: its table marks each role true (several devices) or
    false (one device).
    """
    GROUPS = ('Roles that take several devices', 'Roles that take one device')

    def checked_roles(self):
        text = (HW / 'hardware_check.cfg').read_text(encoding='utf-8')
        roles = re.findall(r"\['(\w+)', '[^']*', (true|false)\]", text)
        return ({role for role, several in roles if several == 'true'},
                {role for role, several in roles if several == 'false'})

    def readme_group(self, heading):
        readme = (HW / 'README.md').read_text(encoding='utf-8')
        section = readme.split('### ' + heading, 1)[1].split('\n#', 1)[0]
        cells = re.findall(r'^\| (`[^|]*`) \|', section, re.MULTILINE)
        return {role for cell in cells for role in re.findall(r'`(\w+)`', cell)}

    def api_group(self, heading):
        paragraphs = API.split('\n\n')
        index = next(i for i, text in enumerate(paragraphs) if text.startswith(heading))
        return set(re.findall(r'`(\w+)`', paragraphs[index + 1]))

    def names_file_group(self, heading):
        lines = (HW / 'hardware_names.cfg').read_text(encoding='utf-8').splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith('# ---- ' + heading))
        roles = set()
        for line in lines[start + 1:]:
            if line.startswith('# ----'):
                break
            if line.startswith('variable_'):
                roles.add(line.split(':', 1)[0][len('variable_'):])
        return roles

    def test_every_role_is_in_exactly_one_group_of_hardware_check(self):
        several, one = self.checked_roles()
        cfg = sections(HW / 'hardware_names.cfg')
        roles = {option[len('variable_'):] for option in cfg['gcode_macro _HARDWARE_VARS']
                 if option.startswith('variable_')}
        self.assertEqual(several | one, roles)
        self.assertEqual(several & one, set())

    def test_the_readme_groups_match_hardware_check(self):
        several, one = self.checked_roles()
        self.assertEqual(self.readme_group(self.GROUPS[0]), several)
        self.assertEqual(self.readme_group(self.GROUPS[1]), one)

    def test_the_api_groups_match_hardware_check(self):
        several, one = self.checked_roles()
        self.assertEqual(self.api_group(self.GROUPS[0]), several)
        self.assertEqual(self.api_group(self.GROUPS[1]), one)

    def test_the_names_file_groups_match_hardware_check(self):
        several, one = self.checked_roles()
        self.assertEqual(self.names_file_group('Several devices'), several)
        self.assertEqual(self.names_file_group('One device'), one)


if __name__ == '__main__':
    unittest.main()
