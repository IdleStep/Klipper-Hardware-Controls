"""Static checks for Klipper config files, shared with Klipper-Chamber-Cooldown.

Catches what the template tests cannot: files Klipper would fail to parse,
broken includes, tab or mixed indentation, trailing whitespace, CRLF endings,
RESPOND messages with stray double quotes or an unquoted PREFIX, options not
written `key: value`, lines past 100 columns, public macros without a
description (Mainsail and Fluidd show it in their macro lists) and
gcode_macro or delayed_gcode options that stock Klipper does not read, which it
rejects at load.

Files that are third-party code kept close to upstream are not passed to it; the
caller lists them.
"""
import configparser
import pathlib
import re

RESPOND_MSG = re.compile(r'\bMSG="[^"]*"\s*$')
RESPOND_PREFIX = re.compile(r'\bPREFIX=(?!")')
OPTION = re.compile(r'([A-Za-z][A-Za-z0-9_]*)(\s*):(\s*)(\S.*)?$')
# One gcode command (STYLE.md: it cannot wrap), including a Jinja call that stands for one.
COMMAND = re.compile(r'_?[A-Z][A-Z0-9_]*( |$)|\{action_')
MAX_COLUMNS = 100
# The options stock Klipper reads in each section type: exact names, then name prefixes.
# It fails to load a config with any other option (a misspelt `descripton` too). Kalico
# reads more, for example description in a delayed_gcode, so a file that loads there can
# still fail on stock Klipper. Section types that are not listed here are not checked.
ALLOWED_OPTIONS = {
    'delayed_gcode': ({'gcode', 'initial_duration'}, ()),
    'gcode_macro': ({'description', 'gcode', 'rename_existing'}, ('variable_',)),
}


def config_files(root, skip=()):
    root = pathlib.Path(root)
    for path in sorted(root.rglob('*.cfg')):
        relative = path.relative_to(root)
        if not any(part.startswith('.') or part in skip for part in relative.parts):
            yield path


def lint_file(path, check_includes=True, max_columns=MAX_COLUMNS):
    """Return the problems of one file; `max_columns=None` turns the width check off."""
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
        is_respond = stripped.upper().startswith('RESPOND ')
        if is_respond and 'MSG=' in stripped and not RESPOND_MSG.search(stripped):
            problems.append(
                'line %d: RESPOND MSG must be one double-quoted string ending the line' % number)
        if is_respond and RESPOND_PREFIX.search(stripped):
            problems.append('line %d: RESPOND PREFIX must be double-quoted' % number)
        option = OPTION.match(line)
        if option and (option.group(2) or (option.group(4) and option.group(3) != ' ')):
            problems.append('line %d: write the option as `key: value` with one space' % number)
        if max_columns and len(line) > max_columns and not COMMAND.match(stripped):
            problems.append('line %d: %d columns, the limit is %d'
                            % (number, len(line), max_columns))
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
            # A section without gcode only sets variables of a macro that another file defines.
            if 'gcode' in cfg[section] and not cfg[section].get('description', '').strip():
                problems.append('[%s] has no description' % section)
        kind, _, name = section.partition(' ')
        if name and kind in ALLOWED_OPTIONS:
            names, prefixes = ALLOWED_OPTIONS[kind]
            unknown = sorted(option for option in cfg[section]
                             if option not in names and not option.startswith(prefixes))
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
