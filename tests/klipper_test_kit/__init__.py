"""Test tools for Klipper and Kalico config repositories.

Nothing in this package knows about one repository: it imports only the standard library and
Jinja, and the repository that uses it says which devices the printer has and which config
files to load. `tests/test_kit.py` checks that it stays that way.
"""
from .simulator import Printer, State, wrap

__all__ = ['Printer', 'State', 'wrap']
