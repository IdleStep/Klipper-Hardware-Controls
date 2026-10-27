"""Run gcode scripts through real Klipper (or Kalico) in batch mode, no hardware.

Batch mode loads the full configuration with Klipper's own parser and Jinja
version, then executes a gcode file. Any config or command error makes klippy
exit non-zero; an unknown command only logs a warning, so the runner treats
'Unknown command' in the log as a failure too. Two limits: delayed_gcode timers
never fire, and a fan's speed only reaches the status when the MCU flushes, which
batch mode never does. Scripts check macro variables, heater targets and the fan
speeds the macros asked for, which klippy/assert.cfg records.

Environment (all three required, else the tests are skipped; set
KLIPPY_REQUIRED=1 to make skipping an error):
  KLIPPER_DIR   firmware source checkout containing klippy/klippy.py
  KLIPPY_DICT   data dictionary from building the linux process MCU
  KLIPPY_PYTHON python with scripts/klippy-requirements.txt installed
"""
import configparser
import os
import pathlib
import subprocess
import tempfile
import unittest

ENV = ['KLIPPER_DIR', 'KLIPPY_DICT', 'KLIPPY_PYTHON']
# Linked beside printer.cfg as klippy-support/ so configs can include assert.cfg.
SUPPORT_DIR = pathlib.Path(__file__).resolve().parent / 'klippy'


def skip_unless_configured(test_case):
    missing = [name for name in ENV if not os.environ.get(name)]
    if missing:
        if os.environ.get('KLIPPY_REQUIRED'):
            raise RuntimeError('KLIPPY_REQUIRED is set but missing: ' + ', '.join(missing))
        test_case.skipTest('real Klipper not configured (%s)' % ', '.join(missing))


def delayed_gcode_as_macro(path, delayed, macro):
    """Config text defining gcode_macro `macro` with the body of a delayed_gcode,
    so a script can run one tick of a timer loop on demand."""
    cfg = configparser.RawConfigParser(delimiters=(':',), interpolation=None)
    cfg.read(path, encoding='utf-8')
    body = cfg['delayed_gcode ' + delayed]['gcode']
    return '[gcode_macro %s]\ngcode:%s\n' % (macro, body.replace('\n', '\n  '))


def run_script(printer_cfg, gcode, links):
    """Run klippy on printer_cfg (text) with gcode (text). `links` maps names to
    directories made available beside printer.cfg (klippy-support/ is always
    added). Returns (exit code, log)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for name, target in dict(links, **{'klippy-support': SUPPORT_DIR}).items():
            (tmp / name).symlink_to(pathlib.Path(target).resolve(), target_is_directory=True)
        (tmp / 'printer.cfg').write_text(printer_cfg, encoding='utf-8')
        (tmp / 'test.gcode').write_text(gcode, encoding='utf-8')
        klippy = pathlib.Path(os.environ['KLIPPER_DIR']).resolve() / 'klippy' / 'klippy.py'
        python = pathlib.Path(os.environ['KLIPPY_PYTHON']).absolute()
        dictionary = pathlib.Path(os.environ['KLIPPY_DICT']).resolve()
        result = subprocess.run(
            [str(python), str(klippy), str(tmp / 'printer.cfg'),
             '-i', str(tmp / 'test.gcode'), '-o', os.devnull,
             '-d', str(dictionary), '-l', str(tmp / 'klippy.log')],
            capture_output=True, text=True, timeout=300)
        log = (tmp / 'klippy.log').read_text(encoding='utf-8', errors='replace')
        return result.returncode, log + result.stdout + result.stderr


def run_script_files(test_case, script_dir, printer_cfg, links):
    """Run every *.gcode in script_dir as a subtest. Scripts named *_fails.gcode
    must make klippy exit with an error; all others must succeed."""
    skip_unless_configured(test_case)
    scripts = sorted(pathlib.Path(script_dir).glob('*.gcode'))
    test_case.assertTrue(scripts, 'no scripts in %s' % script_dir)
    for script in scripts:
        with test_case.subTest(script=script.name):
            code, log = run_script(printer_cfg, script.read_text(encoding='utf-8'), links)
            failed = code != 0 or 'Unknown command:' in log
            if script.stem.endswith('_fails'):
                test_case.assertTrue(failed, 'expected an error from %s' % script.name)
            else:
                test_case.assertFalse(failed, log[-3000:])
