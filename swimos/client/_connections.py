#  Copyright 2015-2021 SWIM.AI inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import asyncio
import websockets

from enum import Enum
from websockets import ConnectionClosed
from swimos.warp._warp import _Envelope
from typing import TYPE_CHECKING, Any
from ._utils import exception_warn

if TYPE_CHECKING:
    from ._downlinks._downlinks import _DownlinkModel
    from ._downlinks._downlinks import _DownlinkView
    from .. import SwimClient


class RetryStrategy:
    async def retry(self) -> bool:
        """
        Wait for a period of time that is defined by the retry strategy.
        """
        return False

    def reset(self):
        pass


class IntervalStrategy(RetryStrategy):

    def __init__(self, retries_limit=None, delay=3) -> None:
        super().__init__()
        self.retries_limit = retries_limit
        self.delay = delay
        self.retries = 0

    async def retry(self) -> bool:
        if self.retries_limit is None or self.retries_limit > self.retries:
            await asyncio.sleep(self.delay)
            self.retries += 1
            return True
        else:
            return False

    def reset(self):
        self.retries = 0


class ExponentialStrategy(RetryStrategy):

    def __init__(self, retries_limit=None, max_interval=16) -> None:
        super().__init__()
        self.retries_limit = retries_limit
        self.max_interval = max_interval
        self.retries = 0

    async def retry(self) -> bool:
        if self.retries_limit is None or self.retries_limit >= self.retries:
            await asyncio.sleep(min(2 ** self.retries, self.max_interval))
            self.retries += 1
            return True
        else:
            return False

    def reset(self):
        self.retries = 0


class _ConnectionPool:

    def __init__(self, client: 'SwimClient', retry_strategy: RetryStrategy = RetryStrategy()) -> None:
        self.__client = client
        self.__connections = dict()
        self.retry_strategy = retry_strategy

    @property
    def _size(self) -> int:
        return len(self.__connections)

    async def _get_connection(self, host_uri: str, scheme: str, keep_linked: bool,
                              keep_synced: bool) -> '_WSConnection':
        """
        Return a WebSocket connection to the given Host URI. If it is a new
        host or the existing connection is closing, create a new connection.

        :param host_uri:        - URI of the connection host.
        :param scheme:          - URI scheme.
        :param keep_linked:     - Whether the link should be automatically re-established after connection failures.
        :param keep_synced:     - Whether the link should synchronize its state with the remote lane.
        :return:                - WebSocket connection.
        """
        connection = self.__connections.get(host_uri)

        if connection is None or connection.status == _ConnectionStatus.CLOSED:
            connection = _WSConnection(self.__client, host_uri, scheme, keep_linked, keep_synced, self.retry_strategy)
            self.__connections[host_uri] = connection

        return connection

    async def _remove_connection(self, host_uri: str) -> None:
        """
        Remove a connection from the pool.

        :param host_uri:        - URI of the connection host.
        """
        connection = self.__connections.get(host_uri)

        if connection:
            self.__connections.pop(host_uri)
            await connection._close()

    async def _add_downlink_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Subscribe a downlink view to a connection from the pool.

        :param downlink_view:   - Downlink view to subscribe to a connection.
        """
        host_uri = downlink_view._host_uri
        scheme = downlink_view._scheme
        keep_linked = downlink_view._keep_linked
        keep_synced = downlink_view._keep_synced
        connection = await self._get_connection(host_uri, scheme, keep_linked, keep_synced)
        downlink_view._connection = connection

        await connection._subscribe(downlink_view)

    async def _remove_downlink_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Unsubscribe a downlink view from a connection from the pool.

        :param downlink_view:   - Downlink view to unsubscribe from a connection.
        """
        connection: '_WSConnection'

        host_uri = downlink_view._host_uri
        connection = self.__connections.get(host_uri)

        if connection:
            await connection._unsubscribe(downlink_view)

            if connection.status == _ConnectionStatus.CLOSED:
                await self._remove_connection(host_uri)


class _WSConnection:

    def __init__(self, client: 'SwimClient', host_uri: str, scheme: str, keep_linked, keep_synced,
                 retry_strategy: RetryStrategy = RetryStrategy()) -> None:
        self.host_uri = host_uri
        self.scheme = scheme
        self.retry_strategy = retry_strategy

        self.connected = asyncio.Event()
        self.websocket = None
        self.status = _ConnectionStatus.CLOSED
        self.auth_message = None
        self.init_message = None

        self.keep_linked = keep_linked
        self.keep_synced = keep_synced

        self.__subscribers = _DownlinkManagerPool()
        self.__authenticated = asyncio.Event()
        self.__client = client

    async def _open(self) -> None:
        if self.status == _ConnectionStatus.CLOSED:
            self.status = _ConnectionStatus.CONNECTING

            while self.status == _ConnectionStatus.CONNECTING:
                try:
                    if self.scheme == "wss":
                        self.websocket = await websockets.connect(self.host_uri, ssl=True)
                        self.retry_strategy.reset()
                        self.status = _ConnectionStatus.IDLE
                    else:
                        self.websocket = await websockets.connect(self.host_uri)
                        self.retry_strategy.reset()
                        self.status = _ConnectionStatus.IDLE
                except Exception as error:
                    if self.should_reconnect() and await self.retry_strategy.retry():
                        exception_warn(error)
                        continue
                    else:
                        self.status = _ConnectionStatus.CLOSED
                        raise error

            self.connected.set()

    async def _close(self) -> None:
        if self.status != _ConnectionStatus.CLOSED:
            self.status = _ConnectionStatus.CLOSED

            if self.websocket:
                self.websocket.close_timeout = 0.1
                await self.websocket.close()
                self.connected.clear()

    def should_reconnect(self) -> bool:
        """
        Return a boolean flag indicating whether the connection should try to reconnect on failure.

        :return:        - True if the connection should try to reconnect on failure.
        """
        return self.keep_linked or self.keep_synced

    def _set_auth_message(self, message: str) -> None:
        """
        Set the initial auth message that gets sent when the underlying downlink is established.
        """

        self.auth_message = message

    async def _send_auth_message(self) -> None:
        """
        Send the initial auth message for the underlying downlink if it is set.
        """
        if self.auth_message is not None:
            await self._send_message(self.auth_message)

    def _set_init_message(self, message: str) -> None:
        """
        Set the initial message that gets sent when the underlying downlink is established.
        """

        self.init_message = message

    async def _send_init_message(self) -> None:
        """
        Send the initial message for the underlying downlink if it is set.
        """
        if self.init_message is not None:
            await self._send_message(self.init_message)

    def _has_subscribers(self) -> bool:
        """
        Check if the connection has any subscribers.

        :return:        - True if there are subscribers. False otherwise.
        """
        return self.__subscribers._size > 0

    async def _subscribe(self, downlink_view: '_DownlinkView') -> None:
        """
        Add a downlink view to the subscriber list of the current connection.
        If this is the first subscriber, open the connection.

        :param downlink_view:   - Downlink view to add to the subscribers.
        """
        if self.__subscribers._size == 0:
            await self._open()

        await self.__subscribers._register_downlink_view(downlink_view)
        await downlink_view._execute_did_open()

    async def _unsubscribe(self, downlink_view: '_DownlinkView') -> None:
        """
        Remove a downlink view from the subscriber list of the current connection.
        If there are no other subscribers, close the connection.

        :param downlink_view:   - Downlink view to remove from the subscribers.
        """

        await self.__subscribers._deregister_downlink_view(downlink_view)
        await downlink_view._execute_did_close()
        if not self._has_subscribers():
            await self._close()

    async def _send_message(self, message: str) -> None:
        """
        Send a string message to the host using a WebSocket connection.
        If the WebSocket connection to the host is not open, open it.

        :param message:         - String message to send to the remote agent.
        """
        if self.websocket is None or self.status == _ConnectionStatus.CLOSED:
            await self._open()

        await self.connected.wait()
        await self.websocket.send(message)

    async def _wait_for_messages(self) -> None:
        """
        Wait for messages from the remote agent and propagate them
        to all subscribers.
        """
        while self.status == _ConnectionStatus.IDLE:
            self.status = _ConnectionStatus.RUNNING
            try:
                while self.status == _ConnectionStatus.RUNNING:
                    message = await self.websocket.recv()
                    response = _Envelope._parse_recon(message)

                    if response._route:
                        await self.__subscribers._receive_message(response)
                    else:
                        await self._receive_message(self.host_uri, response)
            except ConnectionClosed as error:
                exception_warn(error)
                await self._close()
                if self.should_reconnect() and await self.retry_strategy.retry():
                    await self._open()
                    await self._send_auth_message()
                    await self._send_init_message()
                    continue

    async def _receive_message(self, host_uri: str, message: '_Envelope') -> None:
        """
        Receive a host addressed message from the remote host.

        :param host_uri:        - Uri of the remote host.
        :param message:         - Message received from the remote host.
        """

        if message._tag == 'authed':
            await self._receive_authed(host_uri, message)
        elif message._tag == 'deauthed':
            await self._receive_deauthed(host_uri, message)

    async def _receive_authed(self, host_uri: str, message: '_Envelope') -> None:
        """
        Handle an `authed` response message from the remote agent.

        :param host_uri:        - Uri of the remote host.
        :param message:         - Message received from the remote host.
        """
        self.__authenticated.set()
        await self.__client._execute_did_auth(host_uri, message)

    async def _receive_deauthed(self, host_uri: str, message: '_Envelope') -> None:
        """
        Handle a `deauthed` response message from the remote agent.

        :param host_uri:        - Uri of the remote host.
        :param message:         - Message received from the remote host.
        """
        self.__authenticated.clear()
        await self.__client._execute_did_deauth(host_uri, message)


class _ConnectionStatus(Enum):
    CLOSED = 0
    CONNECTING = 1
    IDLE = 2
    RUNNING = 3


class _DownlinkManagerPool:

    def __init__(self) -> None:
        self.__downlink_managers = dict()

    @property
    def _size(self) -> int:
        return len(self.__downlink_managers)

    async def _register_downlink_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Add a downlink view to a downlink manager from the pool with the given node and lane URIs.
        If a downlink manager is not yet created for the given node and lane, create it and add the downlink view.


        :param downlink_view:   - Downlink view to add to a corresponding downlink manager.
        """
        downlink_manager = self.__downlink_managers.get(downlink_view.route)

        if downlink_manager is None:
            downlink_manager = _DownlinkManager(downlink_view._connection)
            self.__downlink_managers[downlink_view.route] = downlink_manager

        await downlink_manager._add_view(downlink_view)

    async def _deregister_downlink_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Remove a downlink view from the corresponding downlink manager if it exists.
        If it is the last downlink view in the given manager, remove the manager from the pool.

        :param downlink_view:   - Downlink view to remove from the corresponding downlink manager.
        """
        downlink_manager: _DownlinkManager

        if downlink_view.route in self.__downlink_managers:
            downlink_manager = self.__downlink_managers.get(downlink_view.route)
            await downlink_manager._remove_view(downlink_view)

            if downlink_manager._view_count == 0:
                self.__downlink_managers.pop(downlink_view.route)

    async def _receive_message(self, message: '_Envelope') -> None:
        """
        Route a received message for the given host URI to the downlink manager for the corresponding
        node and lane URIs.

        :param message:         - Message received from the remote agent.
        """
        downlink_manager: _DownlinkManager

        downlink_manager = self.__downlink_managers.get(message._route)
        if downlink_manager:
            await downlink_manager._receive_message(message)


class _DownlinkManager:

    def __init__(self, connection: '_WSConnection') -> None:
        self.connection = connection
        self.status = _DownlinkManagerStatus.CLOSED
        self.downlink_model = None
        self.registered_classes = dict()
        self.strict = False

        self.__downlink_views = dict()

    @property
    def _view_count(self) -> int:
        return len(self.__downlink_views)

    @property
    def _is_open(self) -> bool:
        return self.status == _DownlinkManagerStatus.OPEN

    async def _open(self) -> None:
        self.downlink_model: _DownlinkModel

        if self.status == _DownlinkManagerStatus.CLOSED:
            self.status = _DownlinkManagerStatus.OPENING
            self.downlink_model._open()
            await self.downlink_model._establish_downlink()
            self.status = _DownlinkManagerStatus.OPEN

    async def _close(self) -> None:
        self.downlink_model: _DownlinkModel

        if self.status != _DownlinkManagerStatus.CLOSED:
            self.status = _DownlinkManagerStatus.CLOSED
            self.downlink_model._close()

    async def _init_downlink_model(self, downlink_view: '_DownlinkView') -> None:
        """
        Initialise a downlink model to the specified node and lane of the remote agent.

        :param downlink_view:       - Downlink view with the information about the remote agent.
        """
        self.downlink_model = await downlink_view._create_downlink_model(self)
        self.downlink_model.connection = self.connection

    async def _add_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Add a downlink view to the manager. If a downlink model is not yet created, create it and open it.

        :param downlink_view:       - Downlink view to add to the manager.
        """
        if self.downlink_model is None:
            await self._init_downlink_model(downlink_view)

        await downlink_view._register_manager(self)

        if self._view_count == 0:
            await self._open()

        self.__downlink_views[hash(downlink_view)] = downlink_view

    async def _remove_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Remove a downlink view from the manager. If it is the last view associated with the manager,
        close the manager.

        :param downlink_view:       - Downlink view to remove from the manager.
        """
        if hash(downlink_view) in self.__downlink_views:
            self.__downlink_views.pop(hash(downlink_view))

            if self._view_count == 0:
                await self._close()

    async def _receive_message(self, message: '_Envelope') -> None:
        """
        Send a received message to the downlink model.

        :param message:             - Received message from the remote agent.
        """
        self.downlink_model: _DownlinkModel

        await self.downlink_model._receive_message(message)

    async def _subscribers_will_receive(self, message: '_Envelope') -> None:
        """
        Execute the `will_receive` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_will_receive(message)

    async def _subscribers_did_receive(self, message: '_Envelope') -> None:
        """
        Execute the `did_receive` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_did_receive(message)

    async def _subscribers_will_link(self) -> None:
        """
        Execute the `will_link` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_will_link()

    async def _subscribers_did_link(self) -> None:
        """
        Execute the `did_link` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_did_link()

    async def _subscribers_will_unlink(self) -> None:
        """
        Execute the `will_unlink` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_will_unlink()

    async def _subscribers_did_unlink(self) -> None:
        """
        Execute the `did_link` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_did_unlink()

    async def _subscribers_will_sync(self) -> None:
        """
        Execute the `will_sync` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_will_sync()

    async def _subscribers_did_sync(self) -> None:
        """
        Execute the `did_sync` method of all downlink views of the downlink manager.
        """
        for view in self.__downlink_views.values():
            await view._execute_did_sync()

    async def _subscribers_did_set(self, current_value: Any, old_value: Any) -> None:
        """
        Execute the `did_set` method of all value downlink views of the downlink manager.

        :param current_value:       - The new value of the downlink.
        :param old_value:           - The previous value of the downlink.
        """
        for view in self.__downlink_views.values():
            await view._execute_did_set(current_value, old_value)

    async def _subscribers_on_event(self, event: Any) -> None:
        """
        Execute the `on_event` method of all event downlink views of the downlink manager.

        :param event:       - Event from the remote lane.
        """

        for view in self.__downlink_views.values():
            await view._execute_on_event(event)

    async def _subscribers_did_update(self, key: Any, new_value: Any, old_value: Any) -> None:
        """
        Execute the `did_update` method of all map downlink views of the downlink manager.

        :param key:                 - The key of the entry.
        :param new_value:           - The new value of entry.
        :param old_value:           - The previous value of the entry.
        """
        for view in self.__downlink_views.values():
            await view._execute_did_update(key, new_value, old_value)

    async def _subscribers_did_remove(self, key: Any, old_value: Any) -> None:
        """
         Execute the `did_remove` method of all map downlink views of the downlink manager.

         :param key:                 - The key of the entry.
         :param old_value:           - The previous value of the entry.
         """
        for view in self.__downlink_views.values():
            await view._execute_did_remove(key, old_value)

    def _close_views(self) -> None:
        """
        Set the status of all downlink views of the current manager to closed.
        """
        for view in self.__downlink_views.values():
            view._is_open = False


class _DownlinkManagerStatus(Enum):
    CLOSED = 0
    OPENING = 1
    OPEN = 2
