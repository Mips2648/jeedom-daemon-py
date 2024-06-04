"""Test class for base config."""

import re
import sys
import os
from unittest.mock import patch, mock_open
import pytest
from aioresponses import aioresponses

sys.path.append(os.path.realpath(os.path.dirname(__file__) + '/..'))

from jeedomdaemon.base_daemon import BaseDaemon # pylint: disable=wrong-import-position
from jeedomdaemon.base_config import BaseConfig # pylint: disable=wrong-import-position
from jeedomdaemon.aio_connector import Publisher

class TestBaseDaemon():
    def _get_test_config(self):
        config = BaseConfig()
        config.parse(['--loglevel', 'info', '--socketport', '42000', '--callback', 'http://localhost/path', '--apikey', 'cnysltyql', '--pid', '/tmp/test_daemon'])
        return config

    @patch("builtins.open", new_callable=mock_open)
    def test_base_daemon_creation(self, dummy_file):
        """
        Test that it can create a basic daemon
        """
        config = self._get_test_config()
        testdaemon = BaseDaemon(config)
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            testdaemon.run()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0

class TestPublisher():

    @pytest.mark.asyncio
    async def test_send_to_jeedom(self):
        pub = Publisher('http://local/', 'cnysltyql')
        with aioresponses() as mocked:
            pattern = re.compile(r'^http://local/\?apikey=.*$')
            mocked.get(pattern, status=200, body='test')
            mocked.post(pattern, status=200, body='test')
            resp = await pub.send_to_jeedom({})
            assert resp == True

    @pytest.mark.asyncio
    async def test_send_to_jeedom_timeout(self):
        pub = Publisher('http://local/', 'cnysltyql')
        with aioresponses() as mocked:
            pattern = re.compile(r'^http://local/\?apikey=.*$')
            mocked.post(pattern, status=200, timeout=True)
            resp = await pub.send_to_jeedom({})
            assert resp == False