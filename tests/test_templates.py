"""Template behavior tests for Hardware Controls, run in the shared simulator.

Run with: python -m unittest discover -s tests -v
Requires Jinja2 3.1.6. No printer access and no hardware commands are transmitted.

Test classes follow the order of the modules they cover: settings, fans, chamber,
leds, sensors, release_steppers, then the optional fan tachometer monitor.
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

    def test_a_printer_without_a_local_file_controls_only_the_stock_devices(self):
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

    def test_the_test_printers_local_file_sets_only_roles_that_exist(self):
        self.assertLessEqual(self.roles(HW / 'tests/klippy/hardware-local.cfg').keys(),
                             self.roles(HW / 'hardware_names.cfg').keys())


class Fans(Responds):
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
        cases = [(0, 0), (.5, 128), (1, 255), (1.1, 3), (50, 128), (100, 255), (.005, 0)]
        for value, expected in cases:
            with self.subTest(value=value):
                printer.run('PART_COOLING', SPEED=value)
                self.assertEqual(printer.commands[-1], 'M106 S%d' % expected)
        self.assertEqual(self.responses(printer), [])

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


class Leds(unittest.TestCase):
    def test_configured_leds_are_set(self):
        printer = Printer()
        printer.state['neopixel discostick'] = State()
        printer.state['output_pin daystick'] = State()
        printer.run('LED_DIM')
        self.assertIn('SET_PIN PIN=daystick VALUE=0.33', printer.commands)
        self.assertTrue(any('RED=0.3098' in command for command in printer.commands))


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


class FanTachMonitor(unittest.TestCase):
    def printer_with_rpm(self, rpm):
        printer = Printer()
        printer.load(HW / 'optional/fan_tach_monitor.cfg')
        printer.state['toolhead'] = wrap({'extruder': 'extruder'})
        printer.state['extruder'] = wrap({'target': 250., 'temperature': 250.})
        printer.state['pause_resume'] = wrap({'is_paused': False})
        printer.state['configfile'].settings['heater_fan hotend_fan'] = wrap({'heater_temp': 50.})
        if rpm != 'missing':
            printer.state['heater_fan hotend_fan'] = wrap({'rpm': rpm})
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
                            'Set hotend_fan in hardware-local.cfg.'),
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
