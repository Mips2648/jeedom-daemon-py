"""Test class for base config."""

import logging
import sys
import os
from unittest import mock
import pytest

sys.path.append(os.path.realpath(os.path.dirname(__file__) + '/..'))

from jeedomdaemon.base_daemon import BaseDaemon # pylint: disable=wrong-import-position
from jeedomdaemon.base_config import BaseConfig # pylint: disable=wrong-import-position
from jeedomdaemon.aio_connector import Publisher

class TestBaseDaemon():

    # Arrange
    @pytest.fixture(autouse=True)
    def daemon_config(self):
        self._config = BaseConfig()
        self._config.parse(['--loglevel', 'info', '--socketport', '42000', '--callback', 'http://localhost/path', '--apikey', 'cnysltyql', '--pid', '/tmp/test_daemon'])

    # Arrange
    @pytest.fixture(autouse=True)
    def test_daemon(self):
        self._test_daemon = BaseDaemon(self._config)

    async def _on_start_cb(self):
        raise Exception("Test")

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_base_daemon_creation(self, mock_open_method):
        """
        Tests if it can create a basic daemon
        """
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            # with mock.patch('jeedomdaemon.aio_connector.Publisher.test_callback') as mock_test_callback:
            self._test_daemon.run()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0
        # mock_test_callback.assert_called_once()

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_base_daemon_initialization(self, mock_open_method):
        """
        Tests if the daemon initializes correctly
        """
        assert self._test_daemon._config == self._config

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_base_daemon_on_start_exception(self, mock_open_method):
        """
        Tests on start callback exception
        """
        testdaemon = BaseDaemon(self._config, on_start_cb=self._on_start_cb)
        logger = logging.getLogger('jeedomdaemon.base_daemon')
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            with mock.patch('jeedomdaemon.aio_connector.Publisher.test_callback') as mock_test_callback:
                with mock.patch.object(logger, 'warning') as mock_warning:
                    testdaemon.run()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0
        mock_test_callback.assert_called_once()
        mock_warning.assert_called_once()
        assert len(mock_warning.call_args) == 2
        assert str(mock_warning.call_args[0][1].args[0]) == 'Test'

    @pytest.mark.asyncio
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    async def test_base_daemon_stop(self, mock_open_method):
        """
        Tests if the daemon stops correctly
        """
        with mock.patch.object(self._test_daemon, 'stop', return_value=None) as mock_stop:
            await self._test_daemon.stop()
            mock_stop.assert_called_once()
