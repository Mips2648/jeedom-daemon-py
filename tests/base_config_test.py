"""Test class for base config."""

import sys
import os
import unittest

sys.path.append(os.path.realpath(os.path.dirname(__file__) + '/..'))

from jeedomdaemon.base_config import BaseConfig # pylint: disable=wrong-import-position

class TestBaseConfig(unittest.TestCase):
    def test_base_config_creation(self):
        """
        Test that it can create a basic config parser
        """
        config = BaseConfig()
        config.parse([])
        self.assertEqual(config.socket_host, "127.0.0.1")

    def test_base_config_parse(self):
        """
        Test that it can parse config
        """
        config = BaseConfig()
        config.parse(['--loglevel', 'info', '--socketport', '42000', '--callback', 'http://localhost/path', '--apikey', 'cnysltyql', '--pid', '123'])
        self.assertEqual(config.log_level, "info")
        self.assertEqual(config.socket_host, "127.0.0.1")
        self.assertEqual(config.socket_port, 42000)
        self.assertEqual(config.callback_url, "http://localhost/path")
        self.assertEqual(config.api_key, "cnysltyql")
        self.assertEqual(config.pid_filename, "123")
        self.assertEqual(config.cycle, 0.5)

    def test_custom_config_parse_with_property(self):
        """
        Test that it can parse config
        """
        class TestConfig(BaseConfig):
            def __init__(self):
                super().__init__()
                self.add_argument("--clientId", type=str)

            @property
            def client_id(self):
                return str(self._args.clientId)

        config = TestConfig()
        config.parse(['--clientId', 'hfldhfsd'])
        self.assertEqual(config.client_id, "hfldhfsd")

    def test_custom_config_parse_without_property(self):
        """
        Test that it can parse config
        """
        class TestConfig(BaseConfig):
            def __init__(self):
                super().__init__()
                self.add_argument("--clientId", type=str)

        config = TestConfig()
        config.parse(['--clientId', 'hfldhfsd'])
        self.assertEqual(config.clientId, "hfldhfsd")



if __name__ == '__main__':
    unittest.main()
