"""Small Klipper macro simulator shared by the IdleStep configuration repositories.

It renders real gcode_macro / delayed_gcode templates with Klipper's Jinja
delimiters and executes the commands they emit against an in-memory printer
state. No printer is contacted. Klipper-Chamber-Cooldown and Klipper-Configs
import this module from their Hardware-Controls checkout, so keep the public
names (State, wrap, Printer, HW_ROOT, HARDWARE_MODULES) stable.

HARDWARE_CONTROLS_ROOT, when set, loads the package configs from another
checkout (cooldown CI uses it to test against the oldest supported release).

Like Klipper, each template sees a snapshot of the printer state taken when it
starts rendering; nested macros render when their command runs.
"""
import ast
import configparser
import copy
import os
import pathlib
import shlex

import jinja2

HW_ROOT = pathlib.Path(
    os.environ.get('HARDWARE_CONTROLS_ROOT') or pathlib.Path(__file__).parents[1]).resolve()
HARDWARE_MODULES = [
    'hardware_names', 'fans', 'chamber', 'leds', 'dump_fan', 'sensors', 'release_steppers']
# The test printers' hardware-local.cfg, included after the modules like a printer's own.
# It lives beside the real-firmware scripts, which include the same file.
HARDWARE_LOCAL = pathlib.Path(__file__).resolve().parent / 'klippy' / 'hardware-local.cfg'
DEFAULT_IDLE_TIMEOUT = 4800.


class State(dict):
    """Dict that also allows attribute access, like Klipper's status objects."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e

    def __setattr__(self, key, value):
        self[key] = value


def wrap(value):
    """Recursively convert dicts to State so templates can use dotted access."""
    if isinstance(value, dict):
        return State({k: wrap(v) for k, v in value.items()})
    if isinstance(value, list):
        return [wrap(v) for v in value]
    return value


def default_state():
    """A Turbo-like printer: heated chamber, bed, part fan, two generic fans, sensors."""
    return wrap({
        'idle_timeout': {'state': 'Idle'},
        'heater_generic chamber': {'target': 55., 'temperature': 55.},
        'heater_bed': {'target': 0., 'temperature': 80.},
        'fan': {'speed': 0.},
        'fan_generic exhaust_fan': {'speed': 0.},
        'fan_generic external_pc': {'speed': 0.},
        'filament_motion_sensor motion_sensor': {'enabled': False},
        'filament_switch_sensor switch_sensor': {'enabled': False},
        'configfile': {'settings': {
            'fan': {'off_below': 0.01},
            'stepper_x': {},
            'stepper_y': {},
            'idle_timeout': {'timeout': DEFAULT_IDLE_TIMEOUT},
        }},
    })


class Printer:
    """Loads macro files and runs commands, recording what was emitted.

    commands  every non-comment line emitted, in order (nested macros included)
    messages  action_respond_info output
    delays    last UPDATE_DELAYED_GCODE duration per ID
    """

    def __init__(self, hardware=True):
        self.state = default_state()
        self.templates = {}
        self.commands = []
        self.messages = []
        self.delays = {}
        self.idle_timeout = DEFAULT_IDLE_TIMEOUT
        self.env = jinja2.Environment(block_start_string='{%', block_end_string='%}',
                                      variable_start_string='{', variable_end_string='}')
        if hardware:
            for name in HARDWARE_MODULES:
                self.load(HW_ROOT / (name + '.cfg'))
            self.load(HARDWARE_LOCAL)

    def load(self, path):
        """Register every macro in a config file; gcode_macro variables become state.

        Like Klipper, a section that is loaded again is merged: its variables replace the
        earlier ones and it keeps the earlier gcode unless it has its own.
        """
        cfg = configparser.RawConfigParser(delimiters=(':',), strict=True)
        cfg.read_string(pathlib.Path(path).read_text(encoding='utf-8'))
        for section in cfg.sections():
            if not section.startswith(('gcode_macro ', 'delayed_gcode ')):
                continue
            kind, name = section.split(' ', 1)
            if cfg.has_option(section, 'gcode') or name.upper() not in self.templates:
                self.templates[name.upper()] = self.env.from_string(cfg[section].get('gcode', ''))
            if kind == 'gcode_macro':
                self.state.setdefault(section, State()).update(
                    wrap({key[len('variable_'):]: ast.literal_eval(value)
                          for key, value in cfg[section].items()
                          if key.startswith('variable_')}))

    def run(self, command, **params):
        """Render a macro and execute what it emits. Returns the rendered text."""
        def raise_error(message):
            raise ValueError(message)

        def respond_info(message):
            self.messages.append(message)
            return ''

        rendered = self.templates[command.upper()].render(
            printer=copy.deepcopy(self.state),
            params=State({k: str(v) for k, v in params.items()}),
            action_raise_error=raise_error,
            action_respond_info=respond_info)
        for line in rendered.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                self.execute(line)
        return rendered

    def execute(self, line):
        """Apply one emitted command to the simulated state."""
        tokens = shlex.split(line)
        name = tokens[0].upper()
        args = dict(token.split('=', 1) for token in tokens[1:] if '=' in token)
        self.commands.append(line)
        if name in self.templates:
            self.run(name, **args)
        elif name == 'SET_GCODE_VARIABLE':
            macro = self.state['gcode_macro ' + args['MACRO']]
            macro[args['VARIABLE']] = wrap(ast.literal_eval(args['VALUE']))
        elif name == 'UPDATE_DELAYED_GCODE':
            self.delays[args['ID']] = float(args['DURATION'])
        elif name == 'SET_IDLE_TIMEOUT':
            self.idle_timeout = float(args['TIMEOUT'])
        elif name == 'SET_HEATER_TEMPERATURE':
            generic = 'heater_generic ' + args['HEATER']
            heater = self.state[generic if generic in self.state else args['HEATER']]
            heater.target = float(args['TARGET'])
        elif name == 'SET_FAN_SPEED':
            self.state['fan_generic ' + args['FAN']].speed = float(args['SPEED'])
        elif name == 'M106':
            self.state['fan'].speed = float(tokens[1][1:]) / 255
        elif name == 'SET_FILAMENT_SENSOR':
            for kind in ['filament_motion_sensor ', 'filament_switch_sensor ']:
                if kind + args['SENSOR'] in self.state:
                    self.state[kind + args['SENSOR']].enabled = bool(int(args['ENABLE']))
