"""Module providing a base class to parse config of your daemon."""

from __future__ import annotations

import argparse
from typing import Sequence

class BaseConfig(object):
    def __init__(self):
        self._args = None
        self.__parser = argparse.ArgumentParser(description='Daemon for Jeedom plugin')
        self.add_argument("--loglevel", help="Log Level for the daemon", type=str, default='error')
        self.add_argument("--sockethost", help="Socket host", type=str, default='127.0.0.1')
        self.add_argument("--socketport", help="Socket Port", type=int, default=0)
        self.add_argument("--callback", help="Jeedom callback url", type=str)
        self.add_argument("--apikey", help="Plugin API Key", type=str)
        self.add_argument("--pid", help="daemon pid", type=str)

    def add_argument(self, *args, **kwargs):
        """Add a, argurment to parse.

        e.g. from your child class:

        self.add_argument("--clientId", type=str)

        self.add_argument("--intValue", type=int)
        """
        return self.__parser.add_argument(*args, **kwargs)

    def parse(self, args: Sequence[str] | None = None):
        """Actually parse de config, it will be done for you at daemon start."""
        if self._args is None:
            self._args = self.__parser.parse_args(args)

    @property
    def callback_url(self):
        """Return the callback url to Jeedom."""
        return str(self._args.callback)

    @property
    def socket_host(self):
        """Return the daemon socket host."""
        return str(self._args.sockethost)

    @property
    def socket_port(self):
        """Return the daemon socket port."""
        return int(self._args.socketport)

    @property
    def log_level(self):
        """Return the log level."""
        return str(self._args.loglevel)

    @property
    def api_key(self):
        """Return the api key."""
        return str(self._args.apikey)

    @property
    def pid_filename(self):
        """Return the pid."""
        return str(self._args.pid)
