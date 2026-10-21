import unittest

from config_lint import lint
from klipper_sim import HW_ROOT


class ConfigLint(unittest.TestCase):
    def test_config_files_are_clean(self):
        self.assertEqual(lint(HW_ROOT), {})


if __name__ == '__main__':
    unittest.main()
