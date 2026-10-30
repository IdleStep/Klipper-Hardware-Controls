"""Template behavior tests for Hardware Controls, run in the shared simulator.

Run with: python -m unittest discover -s tests -v
Requires Jinja2 3.1.6. No printer access and no hardware commands are transmitted.

Test classes follow the order of the modules they cover: settings, fans, chamber,
leds, sensors, release_steppers, hardware_check, then the optional fan tachometer monitor.
"""
import ast
import configparser
import unittest

from klipper_sim import HARDWARE_MODULES, HW_ROOT as HW, Printer, State, wrap


class Responds(unittest.TestCase):
    """Base for test classes that look at the RESPOND commands a macro sent."""

    def responses(self, printer):
        return [command for command in printer.commands if command.startswith('RESPOND')]


class Loading(unittest.TestCase):
    def test_loading_the_package_sends_no_commands(self):
        printer = Printer()
        self.assertEqual(printer.commands, [])
        cfg = configparser.RawConfigParser(delimiters=(':',))
        cfg.read(HW / 'sensors.cfg')
        self.assertNotIn('initial_duration', cfg['delayed_gcode ENABLE_MOTION_SENSOR'])
        self.assertNotIn('delayed_gcode DISABLE_SENSORS', cfg)


class Settings(unittest.TestCase):
    def roles(self, path):
        cfg = configparser.RawConfigParser(delimiters=(':',))
        cfg.read(path, encoding='utf-8')
        return {key: ast.literal_eval(value)
                for key, value in cfg['gcode_macro _HARDWARE_VARS'].items()
                if key.startswith('variable_')}

    def test_a_printer_without_a_names_file_controls_only_the_stock_devices(self):
        printer = Printer(hardware=False)
        for name in HARDWARE_MODULES:
            printer.load(HW / (name + '.cfg'))
        printer.state['neopixel discostick'] = State()
        printer.state['output_pin daystick'] = State()
        for command, params in [('EXHAUST_FAN', {'SPEED': 1}), ('BED_FANS', {'SPEED': 1}),
                                ('EXTERNAL_PC', {'SPEED': 1}), ('CHAMBER', {'TEMP': 40}),
                                ('LED_ON', {}), ('LED_DIM', {}), ('LED_OFF', {}),
                                ('MOTION_SENSOR', {'ENABLE': 0}), ('SWITCH_SENSOR', {'ENABLE': 0})]:
            printer.run(command, **params)
        controls = ('SET_FAN_SPEED', 'SET_HEATER_TEMPERATURE', 'SET_LED', 'SET_PIN',
                    'SET_FILAMENT_SENSOR')
        self.assertEqual([command for command in printer.commands if command.startswith(controls)],
                         [])

    def test_every_role_is_a_name_or_a_list_of_names(self):
        for role, value in self.roles(HW / 'hardware_names.cfg').items():
            with self.subTest(role=role):
                names = value if isinstance(value, list) else [value]
                self.assertTrue(all(isinstance(name, str) for name in names))

    def test_the_test_printers_names_file_sets_only_roles_that_exist(self):
        self.assertLessEqual(self.roles(HW / 'tests/klippy/hardware_names.cfg').keys(),
                             self.roles(HW / 'hardware_names.cfg').keys())


class Fans(Responds):
    def printer_with_a_second_fan(self, value):
        printer = Printer()
        printer.state['fan_generic filter_fan'] = wrap({'speed': 0.})
        printer.state['gcode_macro _HARDWARE_VARS'].exhaust_fan = value
        return printer

    def test_bed_fans_external_pc_and_part_cooling_work_without_an_exhaust_fan(self):
        printer = Printer()
        printer.state.pop('fan_generic exhaust_fan')
        printer.state['fan_generic bed_fans'] = wrap({'speed': 0.})
        printer.run('BED_FANS', SPEED=.4)
        printer.run('EXTERNAL_PC', SPEED=.3)
        printer.run('PART_COOLING', SPEED=50)
        self.assertEqual(printer.state['fan_generic bed_fans'].speed, .4)
        self.assertEqual(printer.state['fan_generic external_pc'].speed, .3)
        self.assertEqual(printer.state['fan'].speed, 128 / 255)

    def test_reset_fans_stops_every_fan_and_the_optional_commands_run(self):
        printer = Printer()
        printer.run('EXHAUST_FAN', SPEED=1)
        printer.run('EXTERNAL_PC', SPEED=.5)
        printer.run('RESET_FANS')
        self.assertEqual(printer.state['fan_generic exhaust_fan'].speed, 0)
        self.assertEqual(printer.state['fan_generic external_pc'].speed, 0)
        for macro in ['LED_ON', 'LED_DIM', 'LED_OFF', 'DUMP_FAN']:
            printer.run(macro)

    def test_part_cooling_takes_a_fraction_or_a_percent(self):
        printer = Printer()
        cases = [(0, 0), (.5, 128), (1, 255), (1.1, 3), (50, 128), (100, 255), (.005, 1)]
        for value, expected in cases:
            with self.subTest(value=value):
                printer.run('PART_COOLING', SPEED=value)
                self.assertEqual(printer.commands[-1], 'M106 S%d' % expected)
        self.assertEqual(self.responses(printer), [])

    def test_part_cooling_leaves_the_minimum_speed_to_the_fan(self):
        printer = Printer()
        printer.state['configfile'].settings['fan'] = wrap({'min_power': .5})
        printer.run('PART_COOLING', SPEED=.1)
        self.assertEqual(printer.commands[-1], 'M106 S26')

    def test_part_cooling_reports_an_invalid_speed_and_stops_the_fan(self):
        for value in [255, 1.05, -1, 'abc', 'nan']:
            with self.subTest(value=value):
                printer = Printer()
                printer.state['fan'].speed = .5
                printer.run('PART_COOLING', SPEED=value)
                self.assertEqual(printer.commands[-1], 'M106 S0')
                self.assertEqual(
                    printer.commands[0],
                    'RESPOND PREFIX="⚠️" MSG="Invalid PART_COOLING value %s, set to 0"' % value)

    def test_a_generic_fan_reports_an_invalid_speed_and_stays_unchanged(self):
        for value in [1.5, -.1, 'abc', 'nan']:
            with self.subTest(value=value):
                printer = Printer()
                printer.state['fan_generic exhaust_fan'].speed = .7
                printer.run('EXHAUST_FAN', SPEED=value)
                self.assertEqual(
                    printer.commands[-1],
                    'RESPOND PREFIX="❌" MSG="Fan speed must be between 0.0 and 1.0 (got %s)"'
                    % value)
                self.assertFalse(any(command.startswith('SET_FAN_SPEED')
                                     for command in printer.commands))
                self.assertEqual(printer.state['fan_generic exhaust_fan'].speed, .7)

    def test_an_invalid_speed_does_not_stop_the_calling_macro(self):
        printer = Printer()
        printer.templates['CALLER'] = printer.env.from_string(
            'EXHAUST_FAN SPEED=2\nEXTERNAL_PC SPEED=0.4')
        printer.run('CALLER')
        self.assertEqual(printer.state['fan_generic external_pc'].speed, .4)


    def test_a_role_with_several_fans_sets_each_one_that_exists(self):
        for value in ['exhaust_fan, filter_fan , missing,',
                      ['exhaust_fan', 'filter_fan', 'missing']]:
            with self.subTest(value=value):
                printer = self.printer_with_a_second_fan(value)
                printer.run('EXHAUST_FAN', SPEED=.6)
                self.assertEqual(
                    [command for command in printer.commands if command.startswith('SET_FAN')],
                    ['SET_FAN_SPEED FAN=exhaust_fan SPEED=0.6',
                     'SET_FAN_SPEED FAN=filter_fan SPEED=0.6'])
                self.assertEqual(printer.state['fan_generic filter_fan'].speed, .6)

    def test_a_single_name_as_a_string_still_names_one_fan(self):
        printer = self.printer_with_a_second_fan('filter_fan')
        printer.run('EXHAUST_FAN', SPEED=.6)
        self.assertEqual(printer.state['fan_generic filter_fan'].speed, .6)
        self.assertEqual(printer.state['fan_generic exhaust_fan'].speed, 0)

    def test_a_role_of_only_separators_or_unknown_names_does_nothing_and_says_nothing(self):
        for value in [' , ', 'missing, nothing', []]:
            with self.subTest(value=value):
                printer = self.printer_with_a_second_fan(value)
                printer.run('EXHAUST_FAN', SPEED=2)
                self.assertFalse(any(command.startswith('SET_FAN') for command in printer.commands))
                self.assertEqual(self.responses(printer), [])

    def test_an_invalid_speed_for_several_fans_is_reported_once_and_changes_none(self):
        printer = self.printer_with_a_second_fan('exhaust_fan, filter_fan')
        printer.run('EXHAUST_FAN', SPEED=2)
        self.assertEqual(self.responses(printer), [
            'RESPOND PREFIX="❌" MSG="Fan speed must be between 0.0 and 1.0 (got 2)"'])
        self.assertFalse(any(command.startswith('SET_FAN_SPEED') for command in printer.commands))

    def test_reset_fans_stops_every_fan_of_a_role_with_several(self):
        printer = self.printer_with_a_second_fan('exhaust_fan, filter_fan')
        printer.run('EXHAUST_FAN', SPEED=1)
        printer.run('RESET_FANS')
        self.assertEqual(printer.state['fan_generic exhaust_fan'].speed, 0)
        self.assertEqual(printer.state['fan_generic filter_fan'].speed, 0)


class Chamber(Responds):
    def test_chamber_sets_the_heater_target(self):
        printer = Printer()
        printer.run('CHAMBER', TEMP=40)
        self.assertEqual(printer.state['heater_generic chamber'].target, 40)
        printer.run('CHAMBER')
        self.assertEqual(printer.state['heater_generic chamber'].target, 0)
        self.assertEqual(self.responses(printer), [])

    def test_chamber_reports_an_invalid_temperature_and_turns_the_heater_off(self):
        for value in ['abc', -5, 'nan']:
            with self.subTest(value=value):
                printer = Printer()
                printer.run('CHAMBER', TEMP=value)
                self.assertEqual(printer.state['heater_generic chamber'].target, 0)
                self.assertEqual(
                    self.responses(printer),
                    ['RESPOND PREFIX="⚠️" MSG="Invalid CHAMBER value %s, set to 0"' % value])


    def test_chamber_gives_every_heater_of_the_role_the_same_target(self):
        for value in ['chamber, upper_chamber , missing', ['chamber', 'upper_chamber', 'missing']]:
            with self.subTest(value=value):
                printer = Printer()
                printer.state['heater_generic upper_chamber'] = wrap({'target': 0.})
                printer.state['gcode_macro _HARDWARE_VARS'].chamber_heater = value
                printer.run('CHAMBER', TEMP=45)
                self.assertEqual(
                    [command for command in printer.commands if command.startswith('SET_HEATER')],
                    ['SET_HEATER_TEMPERATURE HEATER=chamber TARGET=45.0',
                     'SET_HEATER_TEMPERATURE HEATER=upper_chamber TARGET=45.0'])
                printer.run('CHAMBER')
                self.assertEqual(printer.state['heater_generic chamber'].target, 0)
                self.assertEqual(printer.state['heater_generic upper_chamber'].target, 0)

    def test_an_invalid_temperature_is_reported_once_and_turns_every_heater_off(self):
        printer = Printer()
        printer.state['heater_generic upper_chamber'] = wrap({'target': 30.})
        printer.state['gcode_macro _HARDWARE_VARS'].chamber_heater = 'chamber, upper_chamber'
        printer.run('CHAMBER', TEMP='abc')
        self.assertEqual(printer.state['heater_generic chamber'].target, 0)
        self.assertEqual(printer.state['heater_generic upper_chamber'].target, 0)
        self.assertEqual(self.responses(printer),
                         ['RESPOND PREFIX="⚠️" MSG="Invalid CHAMBER value abc, set to 0"'])


class Leds(unittest.TestCase):
    def test_configured_leds_are_set(self):
        printer = Printer()
        printer.state['neopixel discostick'] = State()
        printer.state['output_pin daystick'] = State()
        printer.state['gcode_macro LED_DIM'].neopixel_level = 0.5
        printer.state['gcode_macro LED_DIM'].pin_level = 0.25
        printer.run('LED_DIM')
        self.assertIn('SET_PIN PIN=daystick VALUE=0.25', printer.commands)
        self.assertTrue(any('RED=0.5 ' in command for command in printer.commands))

    def test_the_dim_levels_default_to_0_33_for_both_kinds(self):
        printer = Printer()
        printer.state['neopixel discostick'] = State()
        printer.state['output_pin daystick'] = State()
        printer.run('LED_DIM')
        self.assertIn('SET_PIN PIN=daystick VALUE=0.33', printer.commands)
        self.assertTrue(any('RED=0.33 ' in command for command in printer.commands))

    def test_dim_leaves_a_pin_without_pwm_unchanged_and_says_so(self):
        printer = Printer()
        printer.state['output_pin daystick'] = State()
        printer.state['configfile'].settings['output_pin daystick'] = wrap({'pwm': False})
        printer.run('LED_DIM')
        self.assertFalse(any(command.startswith('SET_PIN') for command in printer.commands))
        self.assertEqual(
            printer.commands,
            ['_HARDWARE_LED LEVEL=0.33 PIN_LEVEL=0.33',
             'RESPOND PREFIX="⚠️" MSG="LED_DIM leaves daystick unchanged - the output pin has no pwm"'])

    def test_on_and_off_set_a_pin_without_pwm(self):
        printer = Printer()
        printer.state['output_pin daystick'] = State()
        printer.state['configfile'].settings['output_pin daystick'] = wrap({'pwm': False})
        printer.run('LED_ON')
        printer.run('LED_OFF')
        self.assertEqual([command for command in printer.commands if command.startswith('SET_PIN')],
                         ['SET_PIN PIN=daystick VALUE=1', 'SET_PIN PIN=daystick VALUE=0'])

    def test_dim_sets_a_pin_with_pwm(self):
        printer = Printer()
        printer.state['output_pin daystick'] = State()
        printer.state['configfile'].settings['output_pin daystick'] = wrap({'pwm': True})
        printer.run('LED_DIM')
        self.assertIn('SET_PIN PIN=daystick VALUE=0.33', printer.commands)


    def test_the_roles_take_a_comma_separated_string_as_well_as_a_list(self):
        for neopixels, pins in [('discostick, th_leds', 'daystick, nightstick'),
                                (['discostick', 'th_leds'], ['daystick', 'nightstick'])]:
            with self.subTest(neopixels=neopixels):
                printer = Printer()
                for name in ['neopixel discostick', 'neopixel th_leds', 'output_pin daystick',
                             'output_pin nightstick']:
                    printer.state[name] = State()
                hw = printer.state['gcode_macro _HARDWARE_VARS']
                hw.led_neopixels = neopixels
                hw.led_pins = pins
                printer.run('LED_ON')
                self.assertEqual(
                    [command for command in printer.commands if command.startswith('SET_')],
                    ['SET_LED LED=discostick RED=1 GREEN=1 BLUE=1 SYNC=0 TRANSMIT=1',
                     'SET_LED LED=th_leds RED=1 GREEN=1 BLUE=1 SYNC=0 TRANSMIT=1',
                     'SET_PIN PIN=daystick VALUE=1', 'SET_PIN PIN=nightstick VALUE=1'])

    def test_a_single_name_as_a_string_is_not_read_one_letter_at_a_time(self):
        printer = Printer()
        printer.state['output_pin daystick'] = State()
        printer.state['output_pin d'] = State()
        printer.state['gcode_macro _HARDWARE_VARS'].led_pins = 'daystick'
        printer.run('LED_ON')
        self.assertEqual([command for command in printer.commands if command.startswith('SET_PIN')],
                         ['SET_PIN PIN=daystick VALUE=1'])


class Sensors(unittest.TestCase):
    def test_the_delayed_callback_enables_the_motion_sensor(self):
        printer = Printer()
        printer.run('ENABLE_MOTION_SENSOR')
        self.assertIn('MOTION_SENSOR ENABLE=1', printer.commands)
        self.assertTrue(printer.state['filament_motion_sensor motion_sensor'].enabled)

    def test_a_mapped_sensor_is_controlled_and_a_missing_one_is_skipped(self):
        printer = Printer()
        printer.state['gcode_macro _HARDWARE_VARS'].motion_sensor = 'encoder'
        printer.state['filament_motion_sensor encoder'] = wrap({'enabled': False})
        printer.run('MOTION_SENSOR', ENABLE=1)
        self.assertTrue(printer.state['filament_motion_sensor encoder'].enabled)
        printer.state.pop('filament_motion_sensor encoder')
        before = len(printer.commands)
        printer.run('MOTION_SENSOR', ENABLE=0)
        self.assertEqual(printer.commands[before:], [])

    def test_a_sensor_value_that_is_not_0_or_1_is_reported_and_leaves_the_sensor_alone(self):
        for macro, sensor in [('MOTION_SENSOR', 'filament_motion_sensor motion_sensor'),
                              ('SWITCH_SENSOR', 'filament_switch_sensor switch_sensor')]:
            for value in ['abc', 'nan', 2, -1, '']:
                with self.subTest(macro=macro, value=value):
                    printer = Printer()
                    printer.state[sensor].enabled = True
                    printer.run(macro, ENABLE=value)
                    self.assertEqual(
                        printer.commands[-1],
                        'RESPOND PREFIX="❌" MSG="%s ENABLE must be 0 or 1 (got %s)"'
                        % (macro, value))
                    self.assertFalse(any(command.startswith('SET_FILAMENT_SENSOR')
                                         for command in printer.commands))
                    self.assertTrue(printer.state[sensor].enabled)

    def test_a_sensor_accepts_0_and_1_in_any_numeric_spelling(self):
        printer = Printer()
        for value, expected in [(0, False), (1, True), ('0.0', False), ('1.0', True)]:
            with self.subTest(value=value):
                printer.run('SWITCH_SENSOR', ENABLE=value)
                self.assertEqual(printer.state['filament_switch_sensor switch_sensor'].enabled,
                                 expected)

    def test_the_saved_sensor_variables_for_pause_and_resume_start_at_zero(self):
        printer = Printer()
        self.assertEqual(printer.state['gcode_macro MOTION_SENSOR'].fmotion_enabled, 0)
        self.assertEqual(printer.state['gcode_macro SWITCH_SENSOR'].fswitch_enabled, 0)
        printer.state['gcode_macro MOTION_SENSOR'].fmotion_enabled = 1
        printer.run('MOTION_SENSOR',
                    ENABLE=printer.state['gcode_macro MOTION_SENSOR'].fmotion_enabled)
        self.assertTrue(printer.state['filament_motion_sensor motion_sensor'].enabled)


class Steppers(unittest.TestCase):
    def test_release_z_and_release_xy_send_their_commands(self):
        printer = Printer()
        printer.run('RELEASE_Z')
        printer.run('RELEASE_XY')
        self.assertIn('M84 Z', printer.commands)
        self.assertIn('SET_STEPPER_ENABLE STEPPER=stepper_x ENABLE=0', printer.commands)
        self.assertIn('SET_STEPPER_ENABLE STEPPER=stepper_y ENABLE=0', printer.commands)

    def test_release_xy_takes_a_comma_separated_string_and_skips_unknown_names(self):
        for value in ['stepper_x, stepper_q ,', ['stepper_x', 'stepper_q']]:
            with self.subTest(value=value):
                printer = Printer()
                printer.state['gcode_macro _HARDWARE_VARS'].release_xy_steppers = value
                printer.run('RELEASE_XY')
                self.assertEqual(
                    [command for command in printer.commands if command.startswith('SET_')],
                    ['SET_STEPPER_ENABLE STEPPER=stepper_x ENABLE=0'])


class HardwareCheck(Responds):
    def printer_with_devices(self):
        printer = Printer()
        for name in ['neopixel discostick', 'neopixel th_leds', 'output_pin daystick',
                     'output_pin plainstick']:
            printer.state[name] = State()
        return printer

    def test_every_named_device_that_exists_is_found(self):
        printer = self.printer_with_devices()
        printer.run('HARDWARE_CHECK')
        self.assertEqual(self.responses(printer)[:3], [
            'RESPOND PREFIX="📃" MSG="chamber_heater - heater_generic chamber found"',
            'RESPOND PREFIX="📃" MSG="chamber_sensor - heater_generic chamber found"',
            'RESPOND PREFIX="📃" MSG="bed_heater - heater_bed found"'])
        self.assertIn('RESPOND PREFIX="📃" MSG="led_pins - output_pin daystick found"',
                      self.responses(printer))
        self.assertEqual(self.responses(printer)[-1],
                         'RESPOND PREFIX="📃" MSG="Hardware check found nothing to fix"')
        self.assertFalse(any('⚠️' in command for command in printer.commands))

    def test_a_role_without_a_device_is_reported_as_off(self):
        printer = self.printer_with_devices()
        printer.state['gcode_macro _HARDWARE_VARS'].bed_fans = ''
        printer.state['gcode_macro _HARDWARE_VARS'].led_neopixels = []
        printer.run('HARDWARE_CHECK')
        self.assertIn('RESPOND PREFIX="📃" MSG="bed_fans - off"', self.responses(printer))
        self.assertIn('RESPOND PREFIX="📃" MSG="led_neopixels - off"', self.responses(printer))

    def test_a_missing_device_a_wrong_form_and_an_unknown_key_are_reported(self):
        printer = self.printer_with_devices()
        hw = printer.state['gcode_macro _HARDWARE_VARS']
        hw.bed_fans = 'bedfans'
        hw.exhaust_fan = 'fan_generic exhaust_fan'
        hw.led_pinz = ['daystick']
        printer.run('HARDWARE_CHECK')
        warnings = [command for command in self.responses(printer) if '⚠️' in command]
        self.assertEqual(warnings, [
            'RESPOND PREFIX="⚠️" MSG="exhaust_fan - fan_generic exhaust_fan starts with the '
            'section type, give only the name after it"',
            'RESPOND PREFIX="⚠️" MSG="bed_fans - fan_generic bedfans not found"',
            'RESPOND PREFIX="⚠️" MSG="led_pinz is not a role - misspelt or removed"',
            'RESPOND PREFIX="⚠️" MSG="Hardware check found 3 to fix"'])

    def test_every_name_in_a_list_is_checked_and_steppers_are_read_from_the_configuration(self):
        printer = self.printer_with_devices()
        hw = printer.state['gcode_macro _HARDWARE_VARS']
        hw.led_neopixels = ['discostick', 'nolights']
        hw.release_xy_steppers = ['stepper_x', 'stepper_q']
        printer.run('HARDWARE_CHECK')
        self.assertEqual([command for command in self.responses(printer) if '⚠️' in command], [
            'RESPOND PREFIX="⚠️" MSG="led_neopixels - neopixel nolights not found"',
            'RESPOND PREFIX="⚠️" MSG="release_xy_steppers - stepper_q not found"',
            'RESPOND PREFIX="⚠️" MSG="Hardware check found 2 to fix"'])
        self.assertIn('RESPOND PREFIX="📃" MSG="release_xy_steppers - stepper_x found"',
                      self.responses(printer))

    def test_every_name_in_a_comma_separated_string_is_checked(self):
        printer = self.printer_with_devices()
        hw = printer.state['gcode_macro _HARDWARE_VARS']
        hw.exhaust_fan = 'exhaust_fan, filter_fan'
        hw.release_xy_steppers = 'stepper_x,stepper_y'
        printer.run('HARDWARE_CHECK')
        self.assertIn('RESPOND PREFIX="📃" MSG="exhaust_fan - fan_generic exhaust_fan found"',
                      self.responses(printer))
        self.assertIn('RESPOND PREFIX="📃" MSG="release_xy_steppers - stepper_y found"',
                      self.responses(printer))
        self.assertEqual([command for command in self.responses(printer) if '⚠️' in command], [
            'RESPOND PREFIX="⚠️" MSG="exhaust_fan - fan_generic filter_fan not found"',
            'RESPOND PREFIX="⚠️" MSG="Hardware check found 1 to fix"'])

    def test_a_role_that_takes_one_device_does_not_split_at_a_comma(self):
        printer = self.printer_with_devices()
        printer.state['gcode_macro _HARDWARE_VARS'].motion_sensor = 'motion_sensor, other'
        printer.run('HARDWARE_CHECK')
        self.assertIn('RESPOND PREFIX="⚠️" MSG="motion_sensor - filament_motion_sensor '
                      'motion_sensor, other not found"', self.responses(printer))

    def test_the_hotend_fan_is_not_checked_without_the_fan_monitor(self):
        printer = self.printer_with_devices()
        printer.state.pop('heater_fan hotend_fan')
        printer.run('HARDWARE_CHECK')
        self.assertIn('RESPOND PREFIX="📃" MSG="hotend_fan - not used, the fan monitor is not '
                      'included"', self.responses(printer))
        self.assertFalse(any('⚠️' in command for command in printer.commands))
        self.assertEqual(self.responses(printer)[-1],
                         'RESPOND PREFIX="📃" MSG="Hardware check found nothing to fix"')

    def test_the_hotend_fan_is_checked_with_the_fan_monitor(self):
        printer = self.printer_with_devices()
        printer.load(HW / 'optional/fan_tach_monitor.cfg')
        printer.state.pop('heater_fan hotend_fan')
        printer.run('HARDWARE_CHECK')
        self.assertEqual([command for command in self.responses(printer) if '⚠️' in command], [
            'RESPOND PREFIX="⚠️" MSG="hotend_fan - heater_fan hotend_fan not found"',
            'RESPOND PREFIX="⚠️" MSG="Hardware check found 1 to fix"'])

    def test_it_changes_nothing(self):
        printer = self.printer_with_devices()
        printer.state['gcode_macro _HARDWARE_VARS'].bed_fans = 'bedfans'
        printer.run('HARDWARE_CHECK')
        self.assertEqual([command for command in printer.commands
                          if not command.startswith('RESPOND')], [])


class FanTachMonitor(unittest.TestCase):
    def printer_with_rpm(self, rpm, min_rpm=8000):
        printer = Printer()
        printer.load(HW / 'optional/fan_tach_monitor.cfg')
        printer.state['toolhead'] = wrap({'extruder': 'extruder'})
        printer.state['extruder'] = wrap({'target': 250., 'temperature': 250.})
        printer.state['pause_resume'] = wrap({'is_paused': False})
        printer.state['gcode_macro HOTEND_FAN_CHECK'].min_rpm = min_rpm
        if rpm == 'missing':
            printer.state.pop('heater_fan hotend_fan')
        else:
            printer.state['heater_fan hotend_fan'].rpm = rpm
        return printer

    def test_a_stopped_fan_pauses_after_three_checks(self):
        printer = self.printer_with_rpm(0.)
        for _ in range(2):
            printer.run('HOTEND_FAN_CHECK')
            self.assertNotIn('PAUSE', printer.commands)
        printer.run('HOTEND_FAN_CHECK')
        self.assertIn('PAUSE', printer.commands)
        self.assertIn('SET_HEATER_TEMPERATURE HEATER=extruder TARGET=0', printer.commands)

    def test_a_stopped_fan_turns_the_hotend_off_when_the_print_is_already_paused(self):
        printer = self.printer_with_rpm(0.)
        printer.state['pause_resume'].is_paused = True
        printer.state['extruder'].target = 250.
        for _ in range(3):
            printer.run('HOTEND_FAN_CHECK')
        self.assertNotIn('PAUSE', printer.commands)
        self.assertIn('SET_HEATER_TEMPERATURE HEATER=extruder TARGET=0', printer.commands)

    def test_the_stoppage_routine_says_what_it_does(self):
        for paused, message in [
                (False, 'Hotend fan stopped, pausing the print and turning the hotend off'),
                (True, 'Hotend fan stopped, turning the hotend off')]:
            with self.subTest(paused=paused):
                printer = self.printer_with_rpm(0.)
                printer.state['pause_resume'].is_paused = paused
                printer.run('FAN_STOPPAGE_ROUTINE')
                self.assertEqual(
                    [command for command in printer.commands if command.startswith('RESPOND')],
                    ['RESPOND PREFIX="❌" MSG="%s"' % message])

    def test_the_rpm_limit_and_the_number_of_stops_are_variables(self):
        printer = self.printer_with_rpm(5000.)
        printer.state['gcode_macro HOTEND_FAN_CHECK'].min_rpm = 4000
        printer.state['gcode_macro HOTEND_FAN_CHECK'].max_consecutive_stops = 1
        printer.run('HOTEND_FAN_CHECK')
        self.assertNotIn('PAUSE', printer.commands)
        printer.state['gcode_macro HOTEND_FAN_CHECK'].min_rpm = 6000
        printer.run('HOTEND_FAN_CHECK')
        self.assertIn('PAUSE', printer.commands)

    def test_each_stopped_check_says_how_many_stops_there_have_been(self):
        printer = self.printer_with_rpm(0.)
        for _ in range(3):
            printer.run('HOTEND_FAN_CHECK')
        stops = [command for command in printer.commands if 'Hotend fan stopped (' in command]
        self.assertEqual(stops, ['RESPOND PREFIX="⚠️" MSG="Hotend fan stopped (%d/3)"' % number
                                 for number in [1, 2, 3]])

    def test_a_running_fan_resets_the_count(self):
        printer = self.printer_with_rpm(0.)
        printer.run('HOTEND_FAN_CHECK')
        printer.state['heater_fan hotend_fan'].rpm = 9000.
        printer.run('HOTEND_FAN_CHECK')
        self.assertEqual(printer.state['gcode_macro _HOTEND_FAN_STATE'].stops, 0)

    def test_a_missing_fan_or_tachometer_is_skipped_and_said_once(self):
        for rpm, message in [
                ('missing', 'Hotend fan is not monitored - no heater_fan hotend_fan exists. '
                            'Set hotend_fan in your hardware_names.cfg.'),
                (None, 'Hotend fan is not monitored - heater_fan hotend_fan has no '
                       'tachometer_pin.')]:
            with self.subTest(rpm=rpm):
                printer = self.printer_with_rpm(rpm)
                for _ in range(5):
                    printer.run('HOTEND_FAN_MONITOR')
                self.assertNotIn('PAUSE', printer.commands)
                self.assertEqual(printer.state['gcode_macro _HOTEND_FAN_STATE'].stops, 0)
                self.assertEqual(
                    [command for command in printer.commands if command.startswith('RESPOND')],
                    ['RESPOND PREFIX="⚠️" MSG="%s"' % message])

    def test_without_a_min_rpm_the_monitor_watches_nothing_and_says_so_once(self):
        printer = self.printer_with_rpm(0., min_rpm=0)
        for _ in range(5):
            printer.run('HOTEND_FAN_MONITOR')
        self.assertNotIn('PAUSE', printer.commands)
        self.assertEqual(printer.state['gcode_macro _HOTEND_FAN_STATE'].stops, 0)
        self.assertEqual(
            [command for command in printer.commands if command.startswith('RESPOND')],
            ['RESPOND PREFIX="⚠️" MSG="Hotend fan is not monitored - min_rpm is not set. '
             'Set it for HOTEND_FAN_CHECK as the README describes."'])

    def test_the_monitor_ships_without_a_min_rpm(self):
        printer = Printer()
        printer.load(HW / 'optional/fan_tach_monitor.cfg')
        self.assertEqual(printer.state['gcode_macro HOTEND_FAN_CHECK'].min_rpm, 0)

    def test_the_hotend_goes_off_before_the_pause_and_the_pause_can_see_its_target(self):
        printer = self.printer_with_rpm(0.)
        printer.templates['PAUSE'] = printer.env.from_string(
            'PAUSE_SAW TARGET={printer["gcode_macro _HOTEND_FAN_STATE"].target}')
        for _ in range(3):
            printer.run('HOTEND_FAN_CHECK')
        off = printer.commands.index('SET_HEATER_TEMPERATURE HEATER=extruder TARGET=0')
        self.assertLess(off, printer.commands.index('PAUSE'))
        self.assertIn('PAUSE_SAW TARGET=250.0', printer.commands)
        self.assertEqual(printer.state['gcode_macro _HOTEND_FAN_STATE'].target, 0)

    def test_a_pause_that_fails_leaves_the_hotend_off_and_the_loop_running(self):
        printer = self.printer_with_rpm(0.)
        printer.templates['PAUSE'] = printer.env.from_string('{action_raise_error("no pause")}')
        for _ in range(2):
            printer.run('HOTEND_FAN_MONITOR')
        with self.assertRaises(ValueError):
            printer.run('HOTEND_FAN_MONITOR')
        self.assertEqual(printer.delays['HOTEND_FAN_MONITOR'], 3)
        self.assertEqual(printer.state['extruder'].target, 0)
        self.assertEqual(printer.state['gcode_macro _HOTEND_FAN_STATE'].target, 250.)
        printer.run('HOTEND_FAN_MONITOR')
        self.assertEqual(printer.state['gcode_macro _HOTEND_FAN_STATE'].target, 0)

    def test_the_loop_is_armed_before_the_check_runs(self):
        printer = self.printer_with_rpm(0.)
        printer.run('HOTEND_FAN_MONITOR')
        arm = 'UPDATE_DELAYED_GCODE ID=HOTEND_FAN_MONITOR DURATION=3'
        self.assertLess(printer.commands.index(arm), printer.commands.index('HOTEND_FAN_CHECK'))

    def test_the_watched_fan_can_have_another_name(self):
        printer = self.printer_with_rpm(0.)
        printer.state['heater_fan nozzle_fan'] = printer.state.pop('heater_fan hotend_fan')
        printer.state['configfile'].settings['heater_fan nozzle_fan'] = (
            printer.state['configfile'].settings.pop('heater_fan hotend_fan'))
        printer.state['gcode_macro _HARDWARE_VARS'].hotend_fan = 'nozzle_fan'
        for _ in range(3):
            printer.run('HOTEND_FAN_CHECK')
        self.assertIn('PAUSE', printer.commands)

    def test_a_fan_that_is_not_the_named_one_is_not_watched(self):
        printer = self.printer_with_rpm(0.)
        printer.state['gcode_macro _HARDWARE_VARS'].hotend_fan = 'nozzle_fan'
        for _ in range(3):
            printer.run('HOTEND_FAN_CHECK')
        self.assertNotIn('PAUSE', printer.commands)
        self.assertIn('no heater_fan nozzle_fan exists', printer.commands[-1])


if __name__ == '__main__':
    unittest.main()
