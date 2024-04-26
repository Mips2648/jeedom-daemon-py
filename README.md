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

pip3 install jeedomdaemon

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
jeedomdaemon~=0.7.3
```

## Quick start

Create a file `myDaemon.py` and copy/past the 4 lines of code below and that's it, nothing else to do, your daemon is good to start.

```python
from jeedomdaemon.base_daemon import BaseDaemon

class myDaemon(BaseDaemon):
    pass

myDaemon().run()
```

Of course, this does nothing so far except starting, accepting incoming requests from your php code and stopping when it is needed.

## What's next

I suggest you to take a look at this [demo plugin](https://github.com/Mips2648/jeedom-aiodemo) which implement this library
