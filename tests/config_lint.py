"""Static checks for Klipper config files, shared with Klipper-Chamber-Cooldown.

Catches what the template tests cannot: files Klipper would fail to parse,
broken includes, tab or mixed indentation, trailing whitespace, CRLF endings,
RESPOND messages with stray double quotes, public macros without a
description (Mainsail and Fluidd show it in their macro lists) and
delayed_gcode options that stock Klipper does not read, which it rejects at load.
"""
import configparser
import pathlib
import re

RESPOND_MSG = re.compile(r'\bMSG="[^"]*"\s*$')
# Kalico also reads description here; stock Klipper fails to load a config that has one.
DELAYED_GCODE_OPTIONS = {'gcode', 'initial_duration'}


def config_files(root, skip=()):
    root = pathlib.Path(root)
    for path in sorted(root.rglob('*.cfg')):
        relative = path.relative_to(root)
        if not any(part.startswith('.') or part in skip for part in relative.parts):
            yield path


def lint_file(path, check_includes=True):
    problems = []
    raw = path.read_bytes()
    if b'\r' in raw:
        problems.append('CRLF line endings')
    text = raw.decode('utf-8')
    if text and not text.endswith('\n'):
        problems.append('no newline at end of file')
    for number, line in enumerate(text.split('\n'), 1):
        if '\t' in line:
            problems.append('line %d: tab character' % number)
        if line != line.rstrip():
            problems.append('line %d: trailing whitespace' % number)
        stripped = line.strip()
        is_respond = stripped.upper().startswith('RESPOND ') and 'MSG=' in stripped
        if is_respond and not RESPOND_MSG.search(stripped):
            problems.append(
                'line %d: RESPOND MSG must be one double-quoted string ending the line' % number)
        include = re.match(r'\[include (.+)\]\s*$', stripped)
        if check_includes and include and not any(char in include.group(1) for char in '*?'):
            if not (path.parent / include.group(1)).exists():
                problems.append('line %d: include target missing: %s' % (number, include.group(1)))
    cfg = configparser.RawConfigParser(delimiters=(':',), strict=True, interpolation=None)
    try:
        cfg.read_string(text, source=str(path))
    except configparser.Error as e:
        problems.append('parse error: %s' % e)
        return problems
    for section in cfg.sections():
        if section.startswith('gcode_macro ') and not section.split(' ', 1)[1].startswith('_'):
            if not cfg[section].get('description', '').strip():
                problems.append('[%s] has no description' % section)
        if section.startswith('delayed_gcode '):
            unknown = sorted(set(cfg[section]) - DELAYED_GCODE_OPTIONS)
            if unknown:
                problems.append('[%s] has options stock Klipper rejects: %s'
                                % (section, ', '.join(unknown)))
    return problems


def lint(root, skip=()):
    """Return {relative path: [problems]} for every config file with problems.

    Includes under tests/ are not resolved: the real-Klipper runner lays those
    configs out beside the packages in a temporary directory."""
    root = pathlib.Path(root)
    found = {}
    for path in config_files(root, skip):
        problems = lint_file(path, check_includes=path.relative_to(root).parts[0] != 'tests')
        if problems:
            found[str(path.relative_to(root))] = problems
    return found
