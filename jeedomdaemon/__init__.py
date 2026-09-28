"""Initialization module for the jeedomdaemon package.

This module exposes the main classes for Jeedom daemon development:
- BaseDaemon: base class to create a Jeedom daemon.
- BaseConfig: base class for daemon configuration.

The __version__ variable indicates the package version.
"""

from .base_daemon import BaseDaemon
from .base_config import BaseConfig

__all__ = ["BaseDaemon", "BaseConfig"]
__version__ = "1.2.9"
