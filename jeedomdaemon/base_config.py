"""Module providing a base class to parse config of your daemon."""

from __future__ import annotations

import argparse
from typing import Sequence

class BaseConfig():
    """Base config class, if you need custom configuration you can inherit from this class

    This class support following argument, you don't need to declare them:
    * --loglevel
    * --sockethost
    * --socketport
    * --callback
    * --apikey
    * --pid
    * --cycle

    If you need additionals arguments then simply create a child class and them in your constructor, e.g.:
        ```
        class MyOwnConfig(BaseConfig):
            def __init__(self):
                super().__init__()

                self.add_argument("--user", help="username", type=str)
                self.add_argument("--password", help="password", type=str)
        ```
    """
    def __init__(self):
        self._args = None
        self.__parser = argparse.ArgumentParser(description='Daemon for Jeedom plugin')
        self.add_argument("--loglevel", help="Log Level for the daemon", type=str, default='error')
        self.add_argument("--sockethost", help="Socket host", type=str, default='127.0.0.1')
        self.add_argument("--socketport", help="Socket Port", type=int, default=0)
        self.add_argument("--callback", help="Jeedom callback url", type=str)
        self.add_argument("--apikey", help="Plugin API Key", type=str)
        self.add_argument("--pid", help="daemon pid", type=str)
        self.add_argument("--cycle", help="cycle", type=float, default=0.5)

    def add_argument(self, *args, **kwargs):
        """Add a, argurment to parse.

        e.g. from your child class:

        * self.add_argument("--clientId", type=str)
        * self.add_argument("--intValue", type=int)
        """
        return self.__parser.add_argument(*args, **kwargs)

    def parse(self, args: Sequence[str] | None = None):
        """Actually parse de config, it will be done for you at daemon start."""
        if self._args is None:
            self._args = self.__parser.parse_args(args)

    def __getattr__(self, name):
        return getattr(self._args, name)

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

    @property
    def cycle(self):
        """Return the cycle."""
        return float(self._args.cycle)
