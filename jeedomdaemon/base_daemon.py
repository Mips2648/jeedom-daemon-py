from __future__ import annotations

import logging
import signal
import os
import sys
import asyncio
import functools
from typing import Callable, Awaitable

from .utils import Utils
from .aio_connector import Publisher, Listener
from .base_config import BaseConfig

class BaseDaemon:
    def __init__(self,
                 config: BaseConfig,
                 on_start_cb: Callable[...,Awaitable[None]] | None = None,
                 on_message_cb: Callable[[list], Awaitable[None]] | None = None,
                 on_stop_cb: Callable[..., None] | None = None,
                 ) -> None:
        self._config = config
        self._config.parse()
        self._listen_task = None
        self._loop = None
        self._logger = logging.getLogger(__name__)
        self.__log_level = Utils.convert_log_level(self._config.log_level)
        self._on_start_cb = on_start_cb
        self._on_message_cb = on_message_cb
        self._on_stop_cb = on_stop_cb

        Utils.init_logger(self._config.log_level)
        logging.getLogger('asyncio').setLevel(logging.WARNING)

    def setLoggerLoglevel(self, loggerName: str):
        logging.getLogger(loggerName).setLevel(self.__log_level)

    @property
    def log_level(self):
        return self.__log_level

    def run(self):
        try:
            self._logger.info('Starting daemon with log level: %s', self._config.log_level)
            Utils.write_pid(str(self._config.pid_filename))

            asyncio.run(self._run())
        except Exception as e:
            self._logger.error('Fatal error: %s', e)
        finally:
            self._logger.info("Shutdown")
            try:
                self._logger.debug("Removing PID file %s", self._config.pid_filename)
                os.remove(self._config.pid_filename)
            except:
                pass

            self._logger.debug("Exit 0")
            sys.stdout.flush()
            sys.exit(0)

    async def _run(self):
        if self._config.socket_port < 1024 or self._config.socket_port>65535:
            raise ValueError()

        self._loop = asyncio.get_running_loop()
        self._listen_task = Listener.create_listen_task(self._config.socket_host, self._config.socket_port, self._on_socket_message)

        async with Publisher(self._config.callback_url, self._config.api_key) as self._jeedom_publisher:
            # self._jeedom_publisher = Publisher(self._config.callback_url, self._config.api_key)
            if not await self._jeedom_publisher.test_callback():
                return

            if self._on_start_cb is not None and asyncio.iscoroutinefunction(self._on_start_cb):
                await self._on_start_cb()

            self._send_task = self._jeedom_publisher.create_send_task()

            await self._add_signal_handler()
            await asyncio.sleep(1) # allow  all tasks to start

            # await asyncio.gather(self._listen_task, self._send_task)
            await self._listen_task

    def __ask_exit(self, sig):
        self._logger.info("Signal %i caught, exiting...", sig)
        if self._on_stop_cb is not None:
            self._on_stop_cb()

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        tasks = asyncio.all_tasks()
        [task.cancel() for task in tasks]
        self._logger.info("Cancelling %i outstanding tasks", len(tasks))
        try:
            asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self._logger.warning("Some exception occured during cancellation: %s", e)

    async def _add_signal_handler(self):
        self._loop.add_signal_handler(signal.SIGINT, functools.partial(self.__ask_exit, signal.SIGINT))
        self._loop.add_signal_handler(signal.SIGTERM, functools.partial(self.__ask_exit, signal.SIGTERM))

    async def _on_socket_message(self, message):
        if message['apikey'] != self._config.api_key:
            self._logger.error('Invalid apikey from socket : %s', message)
            return
        try:
            if self._on_message_cb is not None:
                await self._on_message_cb(message)

        except Exception as e:
            self._logger.error('Send command to demon error: %s', e)