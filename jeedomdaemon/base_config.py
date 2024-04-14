import argparse

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
        return self.__parser.add_argument(*args, **kwargs)

    def parse(self):
        if self._args is None:
            self._args = self.__parser.parse_args()

    @property
    def callback_url(self):
        return str(self._args.callback)

    @property
    def socket_host(self):
        return str(self._args.sockethost)

    @property
    def socket_port(self):
        return int(self._args.socketport)

    @property
    def log_level(self):
        return str(self._args.loglevel)

    @property
    def api_key(self):
        return str(self._args.apikey)

    @property
    def pid_filename(self):
        return str(self._args.pid)