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
from swimos.warp._warp import _Envelope
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._downlinks._downlinks import _DownlinkModel
    from ._downlinks._downlinks import _DownlinkView


class _ConnectionPool:

    def __init__(self) -> None:
        self.__connections = dict()

    @property
    def _size(self) -> int:
        return len(self.__connections)

    async def _get_connection(self, host_uri: str, scheme: str) -> '_WSConnection':
        """
        Return a WebSocket connection to the given Host URI. If it is a new
        host or the existing connection is closing, create a new connection.

        :param host_uri:        - URI of the connection host.
        :param scheme:          - URI scheme.
        :return:                - WebSocket connection.
        """
        connection = self.__connections.get(host_uri)

        if connection is None or connection.status == _ConnectionStatus.CLOSED:
            connection = _WSConnection(host_uri, scheme)
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
        connection = await self._get_connection(host_uri, scheme)
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

    def __init__(self, host_uri: str, scheme: str) -> None:
        self.host_uri = host_uri
        self.scheme = scheme
        self.connected = asyncio.Event()
        self.websocket = None
        self.status = _ConnectionStatus.CLOSED

        self.__subscribers = _DownlinkManagerPool()

    async def _open(self) -> None:
        if self.status == _ConnectionStatus.CLOSED:
            self.status = _ConnectionStatus.CONNECTING

            try:
                if self.scheme == "wss":
                    self.websocket = await websockets.connect(self.host_uri, ssl=True)
                else:
                    self.websocket = await websockets.connect(self.host_uri)
            except Exception as error:
                self.status = _ConnectionStatus.CLOSED
                raise error

            self.status = _ConnectionStatus.IDLE
            self.connected.set()

    async def _close(self) -> None:
        if self.status != _ConnectionStatus.CLOSED:
            self.status = _ConnectionStatus.CLOSED

            if self.websocket:
                self.websocket.close_timeout = 0.1
                await self.websocket.close()
                self.connected.clear()

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

    async def _unsubscribe(self, downlink_view: '_DownlinkView') -> None:
        """
        Remove a downlink view from the subscriber list of the current connection.
        If there are no other subscribers, close the connection.

        :param downlink_view:   - Downlink view to remove from the subscribers.
        """

        await self.__subscribers._deregister_downlink_view(downlink_view)
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

        if self.status == _ConnectionStatus.IDLE:
            self.status = _ConnectionStatus.RUNNING
            try:
                while self.status == _ConnectionStatus.RUNNING:
                    message = await self.websocket.recv()
                    response = _Envelope._parse_recon(message)
                    await self.__subscribers._receive_message(response)
            finally:
                await self._close()


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
