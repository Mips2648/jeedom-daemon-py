"""Module providing a base class for your daemon."""

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
    """Base daemon class for your daemon

    You should inherit your daemon from it and implement the needed functions amongst on_start, on_message and on_stop

        ```
        class MyDaemon(BaseDaemon):
            def __init__(self) -> None:
                # Standard initialisation
                super().__init__(on_start_cb=self.on_start, on_message_cb=self.on_message, on_stop_cb=self.on_stop)

                # Add here any initialisation your daemon would need

            async def on_start(self):
                # if you don't have specific action to do on start, do not create this method
                pass


            async def on_message(self, message: list):
                pass

            async def on_stop(self):
                # if you don't have specific action to do on stop, do not create this method
                pass
        ```

    To send feeback to Jeedom you have 4 possibilities depending your use case.
    If you are in an async method:
        * await self.send_to_jeedom(payload) will send a single message with the given payload
        * await self.add_change(key, value) will add the key/value to the payload of the next cycle

    If not:
        * self.create_task_send_to_jeedom(payload) will send a single message with the given payload
        * self.create_task_add_change(key, value) will add the key/value to the payload of the next cycle
    """
    def __init__(self,
                 config: BaseConfig = BaseConfig(),
                 on_start_cb: Callable[..., Awaitable[None]] | None = None,
                 on_message_cb: Callable[[list], Awaitable[None]] | None = None,
                 on_stop_cb: Callable[..., Awaitable[None]] | None = None,
                 ) -> None:
        self._config = config
        self._config.parse()
        self.__listen_task: asyncio.Task[None] | None = None
        self._loop: asyncio.AbstractEventLoop = None
        self._publisher: Publisher | None = None
        self._logger = logging.getLogger(__name__)
        self.__log_level = Utils.convert_log_level(self._config.log_level)
        self.__on_start_cb = on_start_cb
        self.__on_message_cb = on_message_cb
        self.__on_stop_cb = on_stop_cb

        Utils.init_logger(self._config.log_level)
        logging.getLogger('asyncio').setLevel(logging.WARNING)

    def set_logger_log_level(self, logger_name: str):
        """ Helper function to set the log level to the given logger"""
        logging.getLogger(logger_name).setLevel(self.log_level)

    @property
    def log_level(self):
        """ Return the log level"""
        return self.__log_level

    def run(self):
        """ Run your daemon, this is the function you should call! """
        try:
            self._logger.info('Starting daemon with log level: %s', self._config.log_level)
            Utils.write_pid(str(self._config.pid_filename))

            asyncio.run(self.__run())
        except Exception as ex: # pylint: disable=broad-exception-caught
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            self._logger.error('Fatal error: %s(%s) in %s on line %s', ex, exception_type, filename, line_number)
        finally:
            self._logger.info("Shutdown")
            try:
                self._logger.debug("Removing PID file %s", self._config.pid_filename)
                os.remove(self._config.pid_filename)
            except: # pylint: disable=bare-except
                pass

            self._logger.debug("Exit 0")
            sys.stdout.flush()
            sys.exit(0)

    async def __run(self):
        if self._config.socket_port < 1024 or self._config.socket_port>65535:
            raise ValueError()

        self._loop = asyncio.get_running_loop()
        self.__listen_task = Listener.create_listen_task(self._config.socket_host, self._config.socket_port, self.__on_socket_message)

        async with Publisher(self._config.callback_url, self._config.api_key, self._config.cycle) as self._publisher:
            if not await self._publisher.test_callback():
                return

            if self.__on_start_cb is not None and asyncio.iscoroutinefunction(self.__on_start_cb):
                await self.__on_start_cb()

            self._publisher.create_send_task()

            await self.__add_signal_handler()
            await asyncio.sleep(1) # allow  all tasks to start

            await self.__listen_task

    async def stop(self):
        """ Stop your daemon if need be"""

        if self.__on_stop_cb is not None:
            await self.__on_stop_cb()

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        self._logger.info("Cancelling %i outstanding tasks", len(tasks))
        for task in tasks:
            task.cancel()
        try:
            asyncio.gather(*tasks, return_exceptions=True)
        except BaseException as e: # pylint: disable=broad-exception-caught
            self._logger.warning("Some exception occured during cancellation: %s", e)

    def __ask_exit(self, sig):
        self._logger.info("Signal %i caught, exiting...", sig)
        asyncio.create_task(self.stop())

    async def __add_signal_handler(self):
        self._loop.add_signal_handler(signal.SIGINT, functools.partial(self.__ask_exit, signal.SIGINT))
        self._loop.add_signal_handler(signal.SIGTERM, functools.partial(self.__ask_exit, signal.SIGTERM))

    async def __on_socket_message(self, message):
        if message['apikey'] != self._config.api_key:
            self._logger.error('Invalid apikey from socket : %s', message)
            return
        try:
            if self.__on_message_cb is not None:
                await self.__on_message_cb(message)

        except Exception as e: # pylint: disable=broad-exception-caught
            self._logger.error('Send command to demon error: %s', e)

    async def send_to_jeedom(self, payload):
        """
        Will send the payload provided.
        return true or false if successful
        """
        return await self._publisher.send_to_jeedom(payload)

    def create_task_send_to_jeedom(self, payload):
        """
        Will create a task to with coroutine to send the payload provided.
        """
        self._loop.create_task(self._publisher.send_to_jeedom(payload))

    async def add_change(self, key: str, value):
        """
        Add a key/value pair to the payload of the next cycle, several level can be provided at once by separating key with `::`
        If a key already exists the value will be replaced by the newest
        """
        await self._publisher.add_change(key, value)

    def create_task_add_change(self, key: str, value):
        """
        Will create a task to with coroutine to add a key/value pair to the payload of the next cycle.
        """
        self._loop.create_task(self._publisher.add_change(key, value))
