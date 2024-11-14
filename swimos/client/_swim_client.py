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
import os
import sys
import traceback

from asyncio import Future
from concurrent.futures import CancelledError
from threading import Thread
from traceback import TracebackException
from typing import Callable, Any, Optional
from ._connections import _ConnectionPool, _WSConnection, RetryStrategy, IntervalStrategy
from ._downlinks._downlinks import _ValueDownlinkView, _EventDownlinkView, _DownlinkView, _MapDownlinkView
from ._downlinks._utils import validate_callback
from ._utils import _URI, after_started, exception_warn
from swimos.structures import RecordConverter
from swimos.warp._warp import _CommandMessage, _AuthRequest, _Envelope


class SwimClient:

    def __init__(self, retry_strategy: RetryStrategy = IntervalStrategy(), terminate_on_exception: bool = False,
                 execute_on_exception: Callable = None,
                 debug: bool = False) -> None:
        self.debug = debug
        self.execute_on_exception = execute_on_exception
        self.terminate_on_exception = terminate_on_exception

        self._loop = None
        self._loop_thread = None
        self._has_started = False
        self._did_auth_callback = None
        self._did_deauth_callback = None
        self.authed_hosts = dict()

        self.__connection_pool = _ConnectionPool(self, retry_strategy)

    def did_auth(self, function: Callable) -> 'SwimClient':
        """
        Set the `did_auth` callback of the current client to a given function.

        :param function:   - Function to be called when a remote host is authenticated.
        :return:           - The current Swim client.
        """
        self._did_auth_callback = validate_callback(function)
        return self

    def did_deauth(self, function: Callable) -> 'SwimClient':
        """
        Set the `did_deauth` callback of the current client to a given function.

        :param function:   - Function to be called when a remote host is deauthenticated.
        :return:           - The current Swim client.
        """
        self._did_deauth_callback = validate_callback(function)
        return self

    def __enter__(self) -> 'SwimClient':
        self.start()
        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Exception],
                 exc_traceback: Optional[TracebackException]) -> 'SwimClient':

        if exc_value or exc_traceback:
            self._handle_exception(exc_value, exc_traceback)

        self.stop()
        return self

    def start(self) -> 'SwimClient':
        """
        Start the Swim client.
        Create a new thread and starts an asyncio loop inside it.
        """
        loop = asyncio.new_event_loop()
        asyncio.get_event_loop_policy().set_event_loop(loop)
        self._loop = loop
        self._loop_thread = Thread(target=self.__start_event_loop)
        self._loop_thread.start()
        self._has_started = True

        return self

    def join(self, timeout=None) -> 'SwimClient':
        """
        Wait until the Swim client thread terminates.
        This blocks the calling thread until the Swim client thread terminates
        or until the optional timeout is reached.
        It should be noted that when the timeout is reached, the method returns, but the thread is not terminated.

        :param timeout:        - Time to wait in seconds (Optional).
        """
        self._loop_thread.join(timeout=timeout)

        return self

    def stop(self) -> 'SwimClient':
        """
        Stop the client.
        Schedule a task for stopping the event loop and its thread and afterward close the loop.
        """
        self._schedule_task(self.__stop_event_loop)
        self._loop_thread.join()
        self._loop.close()
        self._has_started = False

        return self

    def command(self, host_uri: str, node_uri: str, lane_uri: str, body: Any):
        """
        Send a command message to a command lane on a remote Swim agent.

        :param host_uri:        - Host URI of the remote agent.
        :param node_uri:        - Node URI of the remote agent.
        :param lane_uri:        - Lane URI of the command lane of the remote agent.
        :param body:            - The message body.
        """

        return self._schedule_task(self.__send_command, host_uri, node_uri, lane_uri, body)

    def authenticate(self, host_uri: str, body: Any):
        """
        Send an authentication request to a remote Swim server.

        :param host_uri:        - Host URI of the remote server.
        :param body:            - The authentication message body.
        """

        self.authed_hosts[host_uri] = asyncio.Event()
        return self._schedule_task(self.__authenticate, host_uri, body)

    def downlink_event(self) -> '_EventDownlinkView':
        """
        Create an Event Downlink.
        """

        return _EventDownlinkView(self)

    def downlink_value(self) -> '_ValueDownlinkView':
        """
        Create a Value Downlink.
        """
        return _ValueDownlinkView(self)

    def downlink_map(self) -> '_MapDownlinkView':
        """
        Create a Map Downlink.
        """
        return _MapDownlinkView(self)

    async def _add_downlink_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Add a DownlinkView to the connection pool of the client.

        :param downlink_view:   - DownlinkView to add to the connection pool.
        """
        await self.__connection_pool._add_downlink_view(downlink_view)

    async def _remove_downlink_view(self, downlink_view: '_DownlinkView') -> None:
        """
        Remove a DownlinkView from the connection pool of the client.

        :param downlink_view:   - DownlinkView to remove from the connection pool.
        """
        await self.__connection_pool._remove_downlink_view(downlink_view)

    async def _get_connection(self, host_uri: str, scheme: str, keep_linked: bool,
                              keep_synced: bool) -> '_WSConnection':
        """
        Get a WebSocket connection to the specified host from the connection pool.

        :param host_uri:        - URI of the host.
        :param scheme:          - URI scheme.
        :param keep_linked:     - Whether the link should be automatically re-established after connection failures.
        :param keep_synced:     - Whether the link should synchronize its state with the remote lane.
        :return:                - WebSocket connection to the host.
        """
        connection = await self.__connection_pool._get_connection(host_uri, scheme, keep_linked, keep_synced)
        return connection

    async def _execute_did_auth(self, host_uri: str, message: '_Envelope') -> None:
        """
        Execute the custom `did_auth` callback of the current Swim client.

        :param host_uri:        - Uri of the remote host.
        :param message:         - Message received from the remote host.
        """
        if self._did_auth_callback:
            self._schedule_task(self._did_auth_callback, host_uri, message)

    async def _execute_did_deauth(self, host_uri: str, message: '_Envelope') -> None:
        """
        Execute the custom `did_deauth` callback of the current Swim client.

        :param host_uri:        - Uri of the remote host.
        :param message:         - Message received from the remote host.
        """
        if self._did_deauth_callback:
            self._schedule_task(self._did_deauth_callback, host_uri, message)

    @after_started
    def _schedule_task(self, task: Callable, *args: Any) -> 'Future':
        """
        Schedule a task for execution in the asyncio loop.

        :param task:            - Coroutine to be executed in the asyncio loop.
        :param args:            - Arguments to be passed to the coroutine.
        :return:                - Future object that holds information about the task execution and final result.
        """
        try:
            future = asyncio.run_coroutine_threadsafe(task(*args), loop=self._loop)
            future.add_done_callback(self.__exception_handler)
            return future
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self._handle_exception(exc_value, exc_traceback)

    def _handle_exception(self, exc_value: Optional[Exception], exc_traceback: Optional[TracebackException]) -> None:
        """
        Report exceptions and schedule custom callbacks or client termination, based on the
        Swim Client policies.

        :param exc_value:       - Exception value.
        :param exc_traceback:   - Exception traceback.
        """
        exception_warn(exc_value)

        if self.debug:
            traceback.print_tb(exc_traceback)

        if self.terminate_on_exception:
            os._exit(1)
            return

        if self.execute_on_exception is not None:
            self.execute_on_exception()

    def __exception_handler(self, future: Future) -> None:
        """
        Check the result of execution of a future and report any exceptions.

        :param future:          - Future that has been completed.
        """
        try:
            future.result()
        except CancelledError:
            pass
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self._handle_exception(exc_value, exc_traceback)

    async def __send_command(self, host_uri: str, node_uri: str, lane_uri: str, body: Any) -> None:
        """
        Send a command message to a given host.

        :param host_uri:        - Host URI of the remote agent.
        :param node_uri:        - Node URI of the remote agent.
        :param lane_uri:        - Lane URI of the command lane of the remote agent.
        :param body:            - The message body.
        """
        record = RecordConverter.get_converter().object_to_record(body)
        host_uri, scheme = _URI._parse_uri(host_uri)
        message = _CommandMessage(node_uri, lane_uri, body=record)
        connection = await self._get_connection(host_uri, scheme, True, False)
        await connection._send_message(message._to_recon())

    async def __authenticate(self, host_uri: str, body: Any) -> None:
        """
        Send an authentication request to a given host.

        :param host_uri:        - Host URI of the remote host.
        :param body:            - The authentication message body.
        """
        record = RecordConverter.get_converter().object_to_record(body)
        host_uri, scheme = _URI._parse_uri(host_uri)
        message = _AuthRequest(body=record)
        connection = await self._get_connection(host_uri, scheme, True, False)
        connection._set_auth_message(message._to_recon())
        await connection._open()
        self._schedule_task(connection._wait_for_messages)
        await connection._send_message(message._to_recon())

    def __start_event_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        asyncio.get_event_loop().run_forever()

    async def __stop_event_loop(self) -> None:
        tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        self._loop.stop()
