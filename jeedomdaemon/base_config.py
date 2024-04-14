class BaseConfig(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    @property
    def callback_url(self):
        return str(self._kwargs.get('callback', ''))

    @property
    def socket_host(self):
        return str(self._kwargs.get('sockethost', '127.0.0.1'))

    @property
    def socket_port(self):
        return int(self._kwargs.get('socketport', 0))

    @property
    def log_level(self):
        return str(self._kwargs.get('loglevel', 'error'))

    @property
    def api_key(self):
        return str(self._kwargs.get('apikey', ''))

    @property
    def pid_filename(self):
        # FIXME: define default pid file
        return str(self._kwargs.get('pid', '/tmp/kroombad.pid'))