"""Render real Klipper templates and execute emitted macro commands in isolation.

Run with: python -m unittest discover -s tests -v
Requires Jinja2 3.1.6. No printer access and no hardware commands are transmitted.
"""
import ast
import configparser
import copy
import pathlib
import shlex
import unittest

import jinja2

ROOT = pathlib.Path(__file__).resolve().parents[1]
HW = ROOT

class State(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e

def wrap(value):
    if isinstance(value, dict):
        return State({k: wrap(v) for k,v in value.items()})
    if isinstance(value,list):
        return [wrap(v) for v in value]
    return value

class Printer:
    def __init__(self, hardware=True, cooldown=False):
        self.state = wrap({'idle_timeout': {'state': 'Idle'}, 'heater_generic chamber': {'target':55., 'temperature':55.},
            'heater_bed': {'target':0., 'temperature':80.}, 'fan': {'speed':0.},
            'fan_generic exhaust_fan': {'speed':0.}, 'fan_generic external_pc': {'speed':0.},
            'filament_motion_sensor motion_sensor': {'enabled':False},
            'filament_switch_sensor switch_sensor': {'enabled':False},
            'configfile': {'settings': {'fan': {'off_below':0.01}, 'stepper_x':{}, 'stepper_y':{}}}})
        self.templates={}
        self.commands=[]
        self.delays={}
        self.messages=[]
        self.env=jinja2.Environment(block_start_string='{%',block_end_string='%}',variable_start_string='{',variable_end_string='}')
        if hardware:
            for name in ['settings','fans','chamber','leds','dump_fan','sensors','release_steppers']:
                self.load(HW / (name+'.cfg'))
        if cooldown:
            for name in ['profiles','materials','engine']:
                self.load(ROOT / (name+'.cfg'))

    def load(self,path):
        cfg=configparser.RawConfigParser(delimiters=(':',),strict=True)
        cfg.read_string(path.read_text(encoding='utf-8'))
        for section in cfg.sections():
            if section.startswith(('gcode_macro ', 'delayed_gcode ')):
                kind,name=section.split(' ',1)
                self.templates[name.upper()]=self.env.from_string(cfg[section].get('gcode',''))
                if kind=='gcode_macro':
                    self.state[section]=wrap({k[9:]:ast.literal_eval(v) for k,v in cfg[section].items() if k.startswith('variable_')})

    def run(self,command,**params):
        def fail(message):
            raise ValueError(message)
        rendered=self.templates[command.upper()].render(printer=copy.deepcopy(self.state),params=State({k:str(v) for k,v in params.items()}),
            action_raise_error=fail,action_respond_info=lambda s:self.messages.append(s) or '')
        for line in rendered.splitlines():
            line=line.strip()
            if not line or line.startswith('#'):
                continue
            tokens=shlex.split(line)
            name=tokens[0].upper()
            args=dict(t.split('=',1) for t in tokens[1:] if '=' in t)
            self.commands.append(line)
            if name in self.templates:
                self.run(name,**args)
            elif name=='SET_GCODE_VARIABLE':
                self.state['gcode_macro '+args['MACRO']][args['VARIABLE']]=wrap(ast.literal_eval(args['VALUE']))
            elif name=='UPDATE_DELAYED_GCODE':
                self.delays[args['ID']]=float(args['DURATION'])
            elif name=='SET_HEATER_TEMPERATURE':
                key='heater_generic '+args['HEATER'] if 'heater_generic '+args['HEATER'] in self.state else args['HEATER']
                self.state[key].target=float(args['TARGET'])
            elif name=='SET_FAN_SPEED':
                self.state['fan_generic '+args['FAN']].speed=float(args['SPEED'])
            elif name=='M106':
                self.state['fan'].speed=float(tokens[1][1:])/255
            elif name=='SET_FILAMENT_SENSOR':
                for kind in ['filament_motion_sensor ','filament_switch_sensor ']:
                    if kind+args['SENSOR'] in self.state:
                        self.state[kind+args['SENSOR']].enabled=bool(int(args['ENABLE']))
        return rendered

class Templates(unittest.TestCase):
    def test_hardware_independent_and_inert(self):
        p=Printer(cooldown=False)
        self.assertEqual(p.commands,[])
        self.assertNotIn('gcode_macro _COOLDOWN_VARS',p.state)
        cfg=configparser.RawConfigParser(delimiters=(':',))
        cfg.read(HW/'sensors.cfg')
        self.assertNotIn('initial_duration',cfg['delayed_gcode ENABLE_MOTION_SENSOR'])
        self.assertNotIn('delayed_gcode disable_sensors',cfg)

    def test_delayed_sensor_calls_control(self):
        p=Printer(cooldown=False)
        p.run('ENABLE_MOTION_SENSOR')
        self.assertIn('MOTION_SENSOR ENABLE=1',p.commands)
        self.assertTrue(p.state['filament_motion_sensor motion_sensor'].enabled)

    def test_sensor_mapping_and_missing(self):
        p=Printer(cooldown=False)
        p.state['gcode_macro _HARDWARE_VARS'].motion_sensor='encoder'
        p.state['filament_motion_sensor encoder']=wrap({'enabled':False})
        p.run('MOTION_SENSOR',ENABLE=1)
        self.assertTrue(p.state['filament_motion_sensor encoder'].enabled)
        p.state.pop('filament_motion_sensor encoder')
        p.run('MOTION_SENSOR',ENABLE=0)

    def test_pause_resume_saved_sensor_variables(self):
        p=Printer(cooldown=False)
        self.assertEqual(p.state['gcode_macro MOTION_SENSOR'].fmotion_enabled,0)
        self.assertEqual(p.state['gcode_macro SWITCH_SENSOR'].fswitch_enabled,0)
        p.state['gcode_macro MOTION_SENSOR'].fmotion_enabled=1
        p.run('MOTION_SENSOR',ENABLE=p.state['gcode_macro MOTION_SENSOR'].fmotion_enabled)
        self.assertTrue(p.state['filament_motion_sensor motion_sensor'].enabled)

    def test_fans_do_not_require_exhaust(self):
        p=Printer(cooldown=False)
        p.state.pop('fan_generic exhaust_fan')
        p.state['fan_generic bed_fans']=wrap({'speed':0.})
        p.run('BED_FANS',SPEED=.4)
        p.run('EXTERNAL_PC',SPEED=.3)
        p.run('PART_COOLING',SPEED=50)
        self.assertEqual(p.state['fan_generic bed_fans'].speed,.4)
        self.assertEqual(p.state['fan_generic external_pc'].speed,.3)

    def test_reset_fans_and_optional_leds(self):
        p=Printer(cooldown=False)
        p.run('EXHAUST_FAN',SPEED=1)
        p.run('EXTERNAL_PC',SPEED=.5)
        p.run('RESET_FANS')
        self.assertEqual(p.state['fan_generic exhaust_fan'].speed,0)
        self.assertEqual(p.state['fan_generic external_pc'].speed,0)
        for macro in ['LED_ON','LED_DIM','LED_OFF','DUMP_FAN']:
            p.run(macro)

    def test_configured_leds(self):
        p=Printer(cooldown=False)
        p.state['neopixel discostick']=State()
        p.state['output_pin daystick']=State()
        p.run('LED_DIM')
        self.assertIn('SET_PIN PIN=daystick VALUE=0.33',p.commands)
        self.assertTrue(any('RED=0.3098' in c for c in p.commands))

    def test_stepper_semantics_no_hardware(self):
        p=Printer(cooldown=False)
        p.run('RELEASE_Z')
        p.run('RELEASE_XY')
        self.assertIn('M84 Z',p.commands)
        self.assertIn('SET_STEPPER_ENABLE STEPPER=stepper_x ENABLE=0',p.commands)
        self.assertIn('SET_STEPPER_ENABLE STEPPER=stepper_y ENABLE=0',p.commands)

if __name__=='__main__':
    unittest.main()
