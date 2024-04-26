# jeedom-daemon-py

![pytest 3.9](https://github.com/Mips2648/jeedom-daemon-py/actions/workflows/pytest-3.9.yml/badge.svg)
![pytest 3.11](https://github.com/Mips2648/jeedom-daemon-py/actions/workflows/pytest-3.11.yml/badge.svg)

## Description

This library provide everything is needed to build a daemon for a plugin for Jeedom in python.

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
jeedomdaemon~=0.7
```
