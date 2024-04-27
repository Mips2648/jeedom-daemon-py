# jeedom-daemon-py

![pytest 3.9](https://github.com/Mips2648/jeedom-daemon-py/actions/workflows/pytest-3.9.yml/badge.svg)
![pytest 3.11](https://github.com/Mips2648/jeedom-daemon-py/actions/workflows/pytest-3.11.yml/badge.svg)

## Description

This library provide everything needed to build a daemon for a plugin for Jeedom in python.
It's possible to get a daemon skeleton by typing literally less than 5 lines of code.

## Requirements

* **Python 3.9+**

## How to install

Make sure to add it in your requirements

### Manually

```bash
pip3 install jeedomdaemon
```

### Via Jeedom core packages.json

```json
{
  "pre-install": {},
  "apt": {
    "python3-pip": {}
  },
  "pip3": {
    "jeedomdaemon": {}
  },
  "npm": {},
  "yarn": {},
  "plugin": {},
  "post-install": {}
}
```

### Via requirements.txt

```txt
jeedomdaemon~=0.7.5
```

## Quick start

Create a file `myDaemon.py` and copy/past the 4 lines of code below and that's it, nothing else to do, your daemon is good to start:

```python
from jeedomdaemon.base_daemon import BaseDaemon

class MyDaemon(BaseDaemon):
    pass

MyDaemon().run()
```

Of course, this does nothing so far except starting, accepting incoming requests from your php code and stopping when it is needed.

So let's add few lines in your daemon class:

```python
from jeedomdaemon.base_daemon import BaseDaemon

class MyDaemon(BaseDaemon):
    def __init__(self) -> None:
        # Standard initialisation
        super().__init__(on_start_cb=self.on_start, on_message_cb=self.on_message, on_stop_cb=self.on_stop)

        # Add here any initialisation your daemon would need

    async def on_start(self):
        """
        This method will be called when your daemon start.
        This is the place where you should create yours tasks, login to remote system, etc
        """
        # if you don't have specific action to do on start, do not create this method
        pass


    async def on_message(self, message: list):
        """
        This function will be called once a message is received from Jeedom; check on api key is done already, just care about your logic
        You must implement the different actions that your daemon can handle.
        """
        pass

    def on_stop(self):
        """
        This callback will be called when daemon need to stop`
        You need to close your remote connexions and cancel background tasks if any here.
        """
        # if you don't have specific action to do on stop, do not create this method
        pass

MyDaemon().run()
```

## Configuration

Without additional work, your daemon will accept following argument when started by your php code:

* --loglevel - a string (Jeedom format) giving the log Level for the daemon
* --sockethost - usually not needed, default is '127.0.0.1'
* --socketport - port on which the daemon will open a tcp socket to listen for incomming message from your php code
* --callback - callback url to use by your daemon to send data to your php code
* --apikey - the apikey use to valid communication
* --pid - the pid filename
* --cycle - a float value giving at which frequency daemon should send request to your PHP code, by default every 0.5s (max)

It will happen that you need to receive some additional values from Jeedom to be able to start your daemon, like a user & password to login somewhere. In that case create a child class like in this example and provide it during daemon initialisation:

```python
from jeedomdaemon.base_daemon import BaseDaemon
from jeedomdaemon.base_config import BaseConfig

class DemoConfig(BaseConfig):
    """This is where you declare your custom argument/configuration

    Remember that all usual arguments are managed by the BaseConfig class already so you only have to take care of yours; e.g. user & password in this case
    """
    def __init__(self):
        super().__init__()

        self.add_argument("--user", type=str, default='Harrison')
        self.add_argument("--password", type=str)

class MyDaemon(BaseDaemon):
    def __init__(self) -> None:
        # provide your custom config class during init
        super().__init__(config=DemoConfig(), on_start_cb=...)

        # ...

```

## What's next

I suggest you to take a look at this [demo plugin](https://github.com/Mips2648/jeedom-aiodemo) which implement this library
