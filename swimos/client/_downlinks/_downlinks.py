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
from asyncio import Future

from collections.abc import Callable
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Any
from swimos.recon import Recon
from swimos.structures import Value, RecordConverter
from swimos.warp._warp import _SyncRequest, _CommandMessage, _Envelope, _LinkRequest
from .._utils import _URI
from ._utils import before_open, UpdateRequest, RemoveRequest, after_open, validate_callback

# Imports for type annotations
if TYPE_CHECKING:
    from .._swim_client import SwimClient
    from .._connections import _DownlinkManager


class _DownlinkModel(ABC):

    def __init__(self, client: 'SwimClient') -> None:
        self.client = client
        self.host_uri = None
        self.node_uri = None
        self.lane_uri = None
        self.task = None
        self.connection = None
        self.linked = asyncio.Event()
        self.downlink_manager = None

    @abstractmethod
    async def _establish_downlink(self) -> None:
        """
        Send a request to the remote agent to establish connection.
        """
        raise NotImplementedError

    @abstractmethod
    async def _receive_event(self, message: '_Envelope') -> None:
        """
        Handle an `event` response message from the remote agent.

        :param message:          - Event response message.
        """
        raise NotImplementedError

    @abstractmethod
    async def _receive_synced(self) -> None:
        """
        Handle a `synced` response message from the remote agent.
        """
        raise NotImplementedError

    def _open(self) -> '_DownlinkModel':
        self.task = self.client._schedule_task(self.connection._wait_for_messages)
        self.task.add_done_callback(self.__close_views)
        return self

    def _close(self) -> '_DownlinkModel':
        self.client._schedule_task(self.__close)
        return self

    async def _receive_message(self, message: '_Envelope') -> None:
        """
        Handle a response message from the remote agent.

        :param message:         - Response message.
        """
        if message._tag == 'linked':
            await self._receive_linked()
        elif message._tag == 'synced':
            await self._receive_synced()
        elif message._tag == 'event':
            await self._receive_event(message)
        elif message._tag == 'unlinked':
            await self._receive_unlinked(message)

    async def _receive_linked(self) -> None:
        """
        Handle a `linked` response message from the remote agent.
        """
        self.linked.set()

    async def _receive_unlinked(self, message: '_Envelope') -> None:
        """
        Handle an `unlinked` response message from the remote agent.

        :param message          - Response message.
        """
        if message._body == Value.absent():
            raise Exception(f'Lane "{self.lane_uri}" was unlinked!')
        elif message._body != message._body._tag == 'laneNotFound':
            raise Exception(f'Lane "{self.lane_uri}" was not found on the remote agent!')

    async def __close(self) -> None:
        self.task.cancel()

    # noinspection PyUnusedLocal
    def __close_views(self, future: Future) -> None:
        if self.downlink_manager is not None:
            self.downlink_manager._close_views()


class _DownlinkView(ABC):

    def __init__(self, client: 'SwimClient') -> None:
        self._client = client
        self._host_uri = None
        self._scheme = None
        self._node_uri = None
        self._lane_uri = None
        self._connection = None
        self._model = None
        self._downlink_manager = None
        self._is_open = False

        self.__registered_classes = dict()
        self.__deregistered_classes = set()
        self.__clear_classes = False
        self.__strict = False

    @property
    def route(self) -> str:
        return f'{self._node_uri}/{self._lane_uri}'

    @property
    def strict(self) -> bool:
        """
        The strict status is used when custom objects are received by the downlink. If the downlink is strict,
        a class of the same name, as the object received, must have been registered with the downlink. If the downlink
        is not strict, a custom object will be created dynamically.

        :return:                    - Whether or not the downlink is strict.
        """
        if self._downlink_manager is None:
            return self.__strict
        else:
            return self._downlink_manager.strict

    @strict.setter
    def strict(self, strict: bool) -> None:
        if self._downlink_manager is None:
            self.__strict = strict
        else:
            self._downlink_manager.strict = strict

    @property
    def registered_classes(self) -> dict:
        if self._downlink_manager is None:
            return self.__registered_classes
        else:
            return self._downlink_manager.registered_classes

    def open(self) -> '_DownlinkView':
        if not self._is_open:
            task = self._client._schedule_task(self._client._add_downlink_view, self)
            if task is not None:
                self._is_open = True

        return self

    def close(self) -> '_DownlinkView':
        if self._is_open:
            self._client._schedule_task(self._client._remove_downlink_view, self)
            self._is_open = False

        return self

    @before_open
    def set_host_uri(self, host_uri: str) -> '_DownlinkView':
        self._host_uri, self._scheme = _URI._parse_uri(host_uri)
        return self

    @before_open
    def set_node_uri(self, node_uri: str) -> '_DownlinkView':
        self._node_uri = node_uri
        return self

    @before_open
    def set_lane_uri(self, lane_uri: str) -> '_DownlinkView':
        self._lane_uri = lane_uri
        return self

    def register_class(self, custom_class: Any) -> None:
        """
        Register a class with the downlink view. The registered classes are used for constructing objects when
        events with custom objects are received by the downlink.

        :param custom_class:        - Class to register.
        """
        self.__register_class(custom_class)

    def register_classes(self, classes_list: list) -> None:
        for custom_class in classes_list:
            self.__register_class(custom_class)

    def deregister_class(self, custom_class: Any) -> None:
        """
        Deregister a class from the downlink view and the downlink manager associated with it.

        :param custom_class:        - Class to deregister.
        """
        if self._downlink_manager is None:
            self.__registered_classes.pop(custom_class.__name__, None)
            self.__deregistered_classes.add(custom_class.__name__)
        else:
            self._downlink_manager.registered_classes.pop(custom_class.__name__, None)

    def deregister_classes(self, classes_list: list) -> None:
        for custom_class in classes_list:
            self.deregister_class(custom_class)

    def deregister_all_classes(self) -> None:
        """
        Deregister all classes from the downlink view and the downlink manager associated with it.
        """
        if self._downlink_manager is not None:
            self.__deregistered_classes.update(set(self._downlink_manager.registered_classes.keys()))
            self._downlink_manager.registered_classes.clear()
        else:
            self.__clear_classes = True
            self.__registered_classes.clear()

    @abstractmethod
    async def _register_manager(self, manager: '_DownlinkManager') -> None:
        """
        Register the current downlink view with a downlink manager.

        :param manager:             - Downlink manager for the current downlink view.
        """
        raise NotImplementedError

    @abstractmethod
    async def _create_downlink_model(self, downlink_manager: '_DownlinkManager') -> '_DownlinkModel':
        """
        Create a downlink model for the current downlink view.

        :param downlink_manager:    - Downlink manager of the current downlink view.
        :return:                    - Downlink model for the current downlink view.
        """
        raise NotImplementedError

    async def _initalise_model(self, manager: '_DownlinkManager', model: '_DownlinkModel') -> None:
        """
        Initialise the given downlink model and manager with the values of the current downlink view.

        :param manager:             - Downlink manager for the current downlink view.
        :param model:               - Downlink model for the current downlink view.
        """
        manager.registered_classes = self.registered_classes
        manager.strict = self.strict
        model.downlink_manager = manager
        model.host_uri = self._host_uri
        model.node_uri = self._node_uri
        model.lane_uri = self._lane_uri

    async def _assign_manager(self, manager: '_DownlinkManager') -> None:
        """
        Assign a downlink manager to the current downlink view and update the manager with the values
        of the downlink view.

        :param manager:             - Downlink manager to assign to the current downlink view.
        """
        self._model = manager.downlink_model
        manager.registered_classes.update(self.registered_classes)

        for klass in self.__deregistered_classes:
            manager.registered_classes.pop(klass)

        if self.__clear_classes:
            manager.registered_classes.clear()

        manager.strict = self.strict
        self._downlink_manager = manager

    def __register_class(self, custom_class: Any) -> None:
        try:
            custom_class()

            if self._downlink_manager is not None:
                self._downlink_manager.registered_classes[custom_class.__name__] = custom_class
            else:
                self.__registered_classes[custom_class.__name__] = custom_class
                self.__deregistered_classes.discard(custom_class.__name__)
        except Exception:
            raise Exception(
                f'Class "{custom_class.__name__}" must have a default constructor or default values for all arguments!')


class _EventDownlinkModel(_DownlinkModel):

    async def _establish_downlink(self) -> None:
        link_request = _LinkRequest(self.node_uri, self.lane_uri)
        await self.connection._send_message(link_request._to_recon())

    async def _receive_event(self, message: _Envelope) -> None:
        converter = RecordConverter.get_converter()
        event = converter.record_to_object(message._body, self.downlink_manager.registered_classes,
                                           self.downlink_manager.strict)

        await self.downlink_manager._subscribers_on_event(event)

    async def _receive_synced(self) -> None:
        raise TypeError('Event downlink does not support synced responses!')


class _EventDownlinkView(_DownlinkView):

    def __init__(self, client: 'SwimClient') -> None:
        super().__init__(client)
        self._on_event_callback = None

    def on_event(self, function: Callable) -> '_EventDownlinkView':
        """
        Set the `on_event` callback of the current downlink view to a given function.

        :param function:   - Function to be called when an event is received by the downlink.
        :return:           - The current downlink view.
        """
        self._on_event_callback = validate_callback(function)
        return self

    async def _register_manager(self, manager: '_DownlinkManager') -> None:
        await self._assign_manager(manager)

    async def _create_downlink_model(self, downlink_manager: '_DownlinkManager') -> '_DownlinkModel':
        model = _EventDownlinkModel(self._client)
        await self._initalise_model(downlink_manager, model)
        return model

    # noinspection PyAsyncCall
    async def _execute_on_event(self, event: Any) -> None:
        """
        Execute the custom `on_event` callback of the current downlink view.

        :param event:       - The event received by the downlink.
        """
        if self._on_event_callback:
            self._client._schedule_task(self._on_event_callback, event)


class _ValueDownlinkModel(_DownlinkModel):

    def __init__(self, client: 'SwimClient') -> None:
        super().__init__(client)
        self._value = Value.absent()
        self._synced = asyncio.Event()

    async def _establish_downlink(self) -> None:
        sync_request = _SyncRequest(self.node_uri, self.lane_uri)
        await self.connection._send_message(sync_request._to_recon())

    async def _receive_event(self, message: '_Envelope') -> None:
        await self.__set_value(message)

    async def _receive_synced(self) -> None:
        self._synced.set()

    async def _send_message(self, message: '_Envelope') -> None:
        """
        Send a message to the remote agent of the downlink.

        :param message:         - Message to send to the remote agent.
        """
        await self.linked.wait()
        await self.connection._send_message(message._to_recon())

    async def _get_value(self) -> Any:
        """
        Get the value of the downlink.

        :return:                - The current value of the downlink.
        """
        return self._value

    async def __set_value(self, message: '_Envelope') -> None:
        """
        Set the value of the the downlink and trigger the `did_set` callback of the downlink subscribers.

        :param message:        - The message from the remote agent.
        :return:
        """
        old_value = self._value
        converter = RecordConverter.get_converter()
        self._value = converter.record_to_object(message._body, self.downlink_manager.registered_classes,
                                                 self.downlink_manager.strict)

        await self.downlink_manager._subscribers_did_set(self._value, old_value)


class _ValueDownlinkView(_DownlinkView):

    def __init__(self, client: 'SwimClient') -> None:
        super().__init__(client)
        self._did_set_callback = None
        self._initialised = asyncio.Event()

    @after_open
    def get(self, wait_sync: bool = False) -> Any:
        """
        Return the value of the downlink.

        :param wait_sync:       - If True, wait for the initial `sync` to be completed before returning.
                                  If False, return immediately.
        :return:                - The value of the Downlink.
        """
        if wait_sync:
            task = self._client._schedule_task(self.__get_value)
            return task.result()
        else:
            return self._value

    @after_open
    def set(self, value: Any, blocking: bool = False) -> None:
        """
        Send a command message to set the value of the lane on the remote agent to the given value.

        :param blocking:        - If True, block until the value has been sent to the server.
        :param value:           - New value for the lane of the remote agent.
        """
        task = self._client._schedule_task(self._send_message, value)

        if blocking:
            task.result()

    def did_set(self, function: Callable) -> '_ValueDownlinkView':
        """
        Set the `did_set` callback of the current downlink view to a given function.

        :param function:   - Function to be called when a value is received by the downlink.
        :return:           - The current downlink view.
        """
        self._did_set_callback = validate_callback(function)
        return self

    @property
    def _value(self) -> 'Any':
        if self._model is None:
            return Value.absent()
        else:
            return self._model._value

    async def _register_manager(self, manager: '_DownlinkManager') -> None:
        await self._assign_manager(manager)

        if manager._is_open:
            await self._execute_did_set(self._model._value, Value.absent())

        self._initialised.set()

    async def _create_downlink_model(self, downlink_manager: '_DownlinkManager') -> '_ValueDownlinkModel':
        model = _ValueDownlinkModel(self._client)
        await self._initalise_model(downlink_manager, model)
        return model

    async def _send_message(self, value: Any) -> None:
        """
        Send a message to the remote agent of the downlink.

        :param value:           - New value for the lane of the remote agent.
        """
        await self._initialised.wait()
        recon = RecordConverter.get_converter().object_to_record(value)
        message = _CommandMessage(self._node_uri, self._lane_uri, recon)

        await self._model._send_message(message)

    # noinspection PyAsyncCall
    async def _execute_did_set(self, current_value: Any, old_value: Any) -> None:
        """
        Execute the custom `did_set` callback of the current downlink view.

        :param current_value:       - The new value of the downlink.
        :param old_value:           - The previous value of the downlink.
        """
        if self._did_set_callback:
            self._client._schedule_task(self._did_set_callback, current_value, old_value)

    async def __get_value(self) -> 'Any':
        await self._initialised.wait()
        return await self._model._get_value()


class _MapDownlinkModel(_DownlinkModel):

    def __init__(self, client: 'SwimClient') -> None:
        super().__init__(client)
        self._map = {}
        self._synced = asyncio.Event()

    async def _establish_downlink(self) -> None:
        sync_request = _SyncRequest(self.node_uri, self.lane_uri)
        await self.connection._send_message(sync_request._to_recon())

    async def _receive_event(self, message: '_Envelope') -> None:
        if message._body._tag == 'update':
            await self.__receive_update(message)
        if message._body._tag == 'remove':
            await self.__receive_remove(message)

    async def _receive_synced(self) -> None:
        self._synced.set()

    async def _send_message(self, message: '_Envelope') -> None:
        """
        Send a message to the remote agent of the downlink.

        :param message:         - Message to send to the remote agent.
        """
        await self.linked.wait()
        await self.connection._send_message(message._to_recon())

    async def _get_value(self, key) -> Any:
        """
        Get a value from the map of the downlink using a given key, after it has been synced.

        :param key              - The key of the entry.
        :return:                - The current value of the downlink.
        """
        return self._map.get(key, (Value.absent(), Value.absent()))[1]

    async def _get_values(self) -> list:
        """
        Get all of the values from the map of the downlink as a list.

        :return:                - A list with all the values from the downlink map.
        """
        return list(self._map.values())

    async def __receive_update(self, message: '_Envelope') -> None:
        key = RecordConverter.get_converter().record_to_object(message._body._get_head().value._get_head().value,
                                                               self.downlink_manager.registered_classes,
                                                               self.downlink_manager.strict)

        value = RecordConverter.get_converter().record_to_object(message._body.get_body(),
                                                                 self.downlink_manager.registered_classes,
                                                                 self.downlink_manager.strict)

        recon_key = Recon.to_string(message._body._get_head().value._get_head().value)
        old_value = await self._get_value(recon_key)

        self._map[recon_key] = (key, value)
        await self.downlink_manager._subscribers_did_update(key, value, old_value)

    async def __receive_remove(self, message: '_Envelope') -> None:
        key = RecordConverter.get_converter().record_to_object(message._body._get_head().value._get_head().value,
                                                               self.downlink_manager.registered_classes,
                                                               self.downlink_manager.strict)

        recon_key = Recon.to_string(message._body._get_head().value._get_head().value)
        old_value = self._map.pop(recon_key, (Value.absent(), Value.absent()))[1]

        await self.downlink_manager._subscribers_did_remove(key, old_value)


class _MapDownlinkView(_DownlinkView):

    def __init__(self, client: 'SwimClient') -> None:
        super().__init__(client)
        self._did_update_callback = None
        self._did_remove_callback = None
        self._initialised = asyncio.Event()

    @after_open
    def get(self, key: Any, wait_sync: bool = False) -> Any:
        if wait_sync:
            task = self._client._schedule_task(self.__get_value, key)
            return task.result()
        else:
            return self._map(key)

    @after_open
    def get_all(self, wait_sync: bool = False) -> list:
        if wait_sync:
            task = self._client._schedule_task(self.__get_all_values)
            return task.result()
        else:
            return self._map(None)

    @after_open
    def put(self, key: Any, value: Any, blocking: bool = False) -> None:
        """
        Send a command message to put the given key and value in the remote map lane.

        :param key:             - Entry key.
        :param value:           - Entry value.
        :param blocking:        - If True, block until the value has been sent to the server.
        """
        task = self._client._schedule_task(self.__put_message, key, value)

        if blocking:
            task.result()

    @after_open
    def remove(self, key: Any, blocking: bool = False) -> None:
        """
        Send a command message to remove the given key from the remote map lane.

        :param key:             - Entry key.
        :param blocking:        - If True, block until the value has been sent to the server.
        """
        task = self._client._schedule_task(self.__remove_message, key)

        if blocking:
            task.result()

    def did_update(self, function: Callable) -> '_MapDownlinkView':
        """
        Set the `did_update` callback of the current downlink view to a given function.

        :param function:   - Function to be called when an update event is received by the downlink.
        :return:           - The current downlink view.
        """
        self._did_update_callback = validate_callback(function)
        return self

    def did_remove(self, function: Callable) -> '_MapDownlinkView':
        """
        Set the `did_remove` callback of the current downlink view to a given function.

        :param function:   - Function to be called when a remove event is received by the downlink.
        :return:           - The current downlink view.
        """
        self._did_remove_callback = validate_callback(function)
        return self

    async def _register_manager(self, manager: '_DownlinkManager') -> None:
        await self._assign_manager(manager)

        if manager._is_open:
            for key, value in self._model._map.values():
                await self._execute_did_update(key, value, Value.absent())

        self._initialised.set()

    async def _create_downlink_model(self, downlink_manager: '_DownlinkManager') -> '_MapDownlinkModel':
        model = _MapDownlinkModel(self._client)
        await self._initalise_model(downlink_manager, model)
        return model

    def _map(self, key: Any) -> [Value, dict]:
        if self._model is None:
            return Value.absent()
        else:
            if key is None:
                return list(self._model._map.values())
            else:
                return self._model._map.get(key, (Value.absent(), Value.absent()))[1]

    # noinspection PyAsyncCall
    async def _execute_did_update(self, key: Any, new_value: Any, old_value: Any) -> None:
        """
        Execute the custom `did_update` callback of the current downlink view.

        :param key:             - The entry key of the item.
        :param new_value:       - The new value of the item.
        :param old_value:       - The current value of the item.
        """
        if self._did_update_callback:
            self._client._schedule_task(self._did_update_callback, key, new_value, old_value)

    # noinspection PyAsyncCall
    async def _execute_did_remove(self, key: Any, old_value: Any) -> None:
        """
        Execute the custom `did_remove` callback of the current downlink view.

        :param key:             - The entry key of the item.
        :param old_value:       - The current value of the item.
        """
        if self._did_remove_callback:
            self._client._schedule_task(self._did_remove_callback, key, old_value)

    async def __get_value(self, key: Any) -> Any:
        await self._initialised.wait()
        return await self._model._get_value(key)

    async def __get_all_values(self) -> list:
        await self._initialised.wait()
        return await self._model._get_values()

    async def __put_message(self, key: Any, value: Any) -> None:
        """
        Send a `put` message to the remote agent of the downlink.

        :param key:             - Key for the new entry in the map lane of the remote agent.
        :param value:           - Value for the new entry in the map lane of the remote agent.
        """
        await self._initialised.wait()

        message = _CommandMessage(self._node_uri, self._lane_uri, UpdateRequest(key, value).to_record())
        await self._model._send_message(message)

    async def __remove_message(self, key: Any) -> None:
        """
        Send a `remove` message to the remote agent of the downlink.

        :param key:             - Key for the entry in the map lane that should be removed from the remote agent.
        """
        await self._initialised.wait()

        message = _CommandMessage(self._node_uri, self._lane_uri, RemoveRequest(key).to_record())
        await self._model._send_message(message)
