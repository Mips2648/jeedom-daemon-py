"""Module providing Listener and Publisher classes for your daemon.

This module defines asynchronous classes for socket communication and HTTP publishing
to interact with Jeedom.
"""

import datetime
import logging
import json
import asyncio
from typing import Callable, Awaitable
import aiohttp

DEFAULT_MAX_CHANGES_PER_CYCLE = 5000
DEFAULT_MAX_PAYLOAD_SIZE = 512 * 1024


class Listener():
    """
    This class allows to create an asyncio task that will open a socket server and listen to it until the task is canceled.
    `on_message` callback will be called with the message as a list as argument
    """
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, socket_host: str, socket_port: int, on_message_cb: Callable[[list], Awaitable[None]]) -> None:
        self._socket_host = socket_host
        self._socket_port = socket_port
        self._on_message_cb = on_message_cb
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def create_listen_task(socket_host: str, socket_port: int, on_message_cb: Callable[[list], Awaitable[None]]):
        """ Helper function to create the listen task"""
        listener = Listener(socket_host, socket_port, on_message_cb)
        return asyncio.create_task(listener.listen())

    async def listen(self):
        """ listen function, a task should be made out of it. Don't use this function directly but use `create_listen_task()` instead"""
        try:
            server = await asyncio.start_server(self.__handle_read, self._socket_host, port=self._socket_port)

            async with server:
                self._logger.info('Listening on %s:%s', self._socket_host, self._socket_port)
                await server.serve_forever()
        except asyncio.CancelledError:
            self._logger.info("Listening cancelled")

    async def __handle_read(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._logger.debug("Received new message on socket")
        data = await reader.read()
        message = data.decode()
        writer.close()
        self._logger.debug("Close connection")
        await writer.wait_closed()
        await self._on_message_cb(json.loads(message))


class Publisher():
    """This class allows to push information to Jeedom.

    It can be done either immediately by calling function `send_to_jeedom` or in cycle by calling function `add_change`.

    For the "cycle" mode, a task must be created by calling `create_send_task`

    Pending changes are stored flat (full key -> value) and are split in batches limited by both
    `max_changes_per_cycle` and `max_payload_size`; the nested structure expected by Jeedom is rebuilt at send time.
    """

    def __init__(self, callback_url: str, api_key: str, cycle: float = 0.5,
                 max_changes_per_cycle: int = DEFAULT_MAX_CHANGES_PER_CYCLE,
                 max_payload_size: int = DEFAULT_MAX_PAYLOAD_SIZE) -> None:
        self._jeedom_session = aiohttp.ClientSession()
        self._callback_url = callback_url
        self._api_key = api_key
        self._cycle = cycle if (cycle > 0 and cycle < 10) else 0.5
        self._max_changes_per_cycle = max_changes_per_cycle if max_changes_per_cycle > 0 else DEFAULT_MAX_CHANGES_PER_CYCLE
        self._max_payload_size = max_payload_size if max_payload_size > 0 else DEFAULT_MAX_PAYLOAD_SIZE
        self._logger = logging.getLogger(__name__)

        # short delay used to drain a non-empty queue faster than the nominal cycle
        self._drain_cycle = min(self._cycle / 10, 0.05)

        self.__changes: dict = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._jeedom_session.close()

    @property
    def changes(self):
        """Returns the pending changes as the nested structure that would be sent to Jeedom."""
        return self.__build_nested(self.__changes)

    def create_send_task(self):
        """ Helper function to create the send task.

        A running loop in the current thread must exist
        """
        return asyncio.create_task(self.__send_task())

    async def test_callback(self):
        """test_callback will return true if the communication with Jeedom is successful or false otherwise"""
        try:
            async with self._jeedom_session.get(self._callback_url + '?test=1&apikey=' + self._api_key) as resp:
                if resp.status != 200:
                    self._logger.error("Please check your network configuration page: %s-%s", resp.status, resp.reason)
                    return False
        except aiohttp.ClientError as e:
            self._logger.error('Callback error: %s. Please check your network configuration page', e)
            return False
        return True

    async def __send_task(self):
        self._logger.info("Send async started with a cycle of %ss", self._cycle)
        try:
            last_send_on_error = False
            while True:
                delay = self._cycle
                batch = self._build_batch()
                if len(batch) > 0:
                    try:
                        if len(self.__changes) > 0:
                            self._logger.info("Sending batch of %d changes; %d remaining", len(batch), len(self.__changes))
                        if not await self.send_to_jeedom(self.__build_nested(batch)):
                            self._requeue(batch)
                        elif len(self.__changes) > 0:
                            delay = self._drain_cycle
                    except aiohttp.ClientError as e:
                        if last_send_on_error:
                            self._logger.error("error during send: %s", e)
                        else:
                            self._logger.debug("first time error during send: %s", e)
                            last_send_on_error = True
                        self._requeue(batch)
                    except TypeError as e:
                        self._logger.error("error during send: %s. No new try to send!", e)
                    else:
                        last_send_on_error = False
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            self._logger.info("Send async cancelled")

    def _build_batch(self) -> dict:
        """Extract the next batch of pending changes (flat dict), honouring both configured limits.

        A value which alone exceeds the size limit is sent on its own instead of blocking the queue.
        """
        batch = {}
        size = 0
        for key, value in self.__changes.items():
            if len(batch) >= self._max_changes_per_cycle:
                self._logger.debug("Reached max changes per cycle: %d", self._max_changes_per_cycle)
                break
            item_size = self.__estimate_size(key, value)
            if len(batch) > 0 and size + item_size > self._max_payload_size:
                self._logger.debug("Reached max payload size: %d", self._max_payload_size)
                break
            batch[key] = value
            size += item_size

        for key in batch:
            del self.__changes[key]
        return batch

    def _requeue(self, batch: dict):
        """Put back a failed batch without overwriting values updated in the meantime."""
        for key, value in batch.items():
            self.__changes.setdefault(key, value)

    def __estimate_size(self, key: str, value) -> int:
        try:
            serialized = json.dumps(value, default=lambda d: self.__encoder(d))
        except (TypeError, OverflowError, ValueError):
            serialized = str(value)
        return len(key) + len(serialized) + 8

    @staticmethod
    def __build_nested(flat_changes: dict) -> dict:
        nested = {}
        for key, value in flat_changes.items():
            if key.find('::') == -1:
                nested[key] = value
                continue
            parts = key.split('::')
            node = nested
            for part in parts[:-1]:
                child = node.get(part)
                if not isinstance(child, dict):
                    child = {}
                    node[part] = child
                node = child
            node[parts[-1]] = value
        return nested

    def __encoder(self, obj):
        try:
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            if isinstance(obj, type(None)):
                return None
            return str(obj)
        except Exception as e:
            self._logger.error('Error encoding %s of type %s: %s', str(obj), type(obj), e)
            raise TypeError('Payload is not JSON serializable and no custom encoder is available')

    def __encode_payload(self, payload):
        return json.loads(json.dumps(payload, default=lambda d: self.__encoder(d)))

    def __is_serializable(self, x):
        try:
            json.dumps(x)
            return True
        except (TypeError, OverflowError):
            return False

    async def send_to_jeedom(self, payload):
        """
        Will send the payload provided.
        return true if successful or false otherwise
        """
        self._logger.debug('Try sending to jeedom: %s', payload)
        if not self.__is_serializable(payload):
            self._logger.info('Payload is not JSON serializable. Use custom encoder.')
            payload = self.__encode_payload(payload)
        try:
            async with self._jeedom_session.post(self._callback_url + '?apikey=' + self._api_key, json=payload) as resp:
                if resp.status != 200:
                    self._logger.error('Error on send request to jeedom, return %s-%s', resp.status, resp.reason)
                    return False
            return True
        except asyncio.TimeoutError:
            self._logger.warning('Timeout on send request to jeedom')
            return False

    async def add_change(self, key: str, value):
        """
        Add a key/value pair to the payload of the next cycle, several levels can be provided at once by separating keys with `::`
        If a key already exists the value will be replaced by the newest, keeping its position in the queue; None value will be ignored
        """
        if value is None:
            return

        self.__changes[key] = value
