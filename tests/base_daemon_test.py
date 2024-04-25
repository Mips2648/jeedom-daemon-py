"""Test class for base config."""

import sys
import os
import unittest

sys.path.append(os.path.realpath(os.path.dirname(__file__) + '/..'))

from jeedomdaemon.base_daemon import BaseDaemon # pylint: disable=wrong-import-position
from jeedomdaemon.base_config import BaseConfig # pylint: disable=wrong-import-position

class TestBaseConfig(unittest.TestCase):
    def test_base_daemon_creation(self):
        """
        Test that it can create a basic config parser
        """
        config = BaseConfig()
        config.parse([])
        BaseDaemon(config)

if __name__ == '__main__':
    unittest.main()
