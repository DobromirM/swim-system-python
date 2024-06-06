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
from typing import Any
from unittest.mock import MagicMock
from swimos.client._connections import _ConnectionStatus
from swimos.structures._structs import _Item


class CustomString:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other

    def __str__(self):
        return f'CustomString({self.value})'


class CustomItem(_Item):
    @property
    def key(self) -> 'Any':
        return 'MockKey'

    @property
    def value(self) -> 'Any':
        return 'MockVale'


class MockAsyncFunction(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(MockAsyncFunction, self).__call__(*args, **kwargs)


class MockWebsocketConnect(MagicMock):

    async def __call__(self, *args, **kwargs):
        return super(MockWebsocketConnect, self).__call__(*args, **kwargs)

    @property
    def return_value(self):
        return MockWebsocket.get_mock_websocket()

    @staticmethod
    def set_raise_exception(state):
        MockWebsocket.get_mock_websocket().raise_exception = state


class MockWebsocketConnectException(MagicMock):

    async def __call__(self, *args, **kwargs):
        return super(MockWebsocketConnectException, self).__call__(*args, **kwargs)

    @property
    def return_value(self):
        raise Exception('Mock_websocket_connect_exception')


class MockDownlink:
    instance = None

    def __init__(self):
        self.all_messages_sent = asyncio.Event()
        self.call_counts_left = 0

    async def receive_message(self):

        self.call_counts_left = self.call_counts_left - 1

        if self.call_counts_left == 0:
            self.all_messages_sent.set()

    @staticmethod
    def get_mock_downlink():
        if MockDownlink.instance is None:
            MockDownlink.instance = MockDownlink()

        return MockDownlink.instance

    @staticmethod
    def clear():
        MockDownlink.instance = None


class MockReceiveMessage(MagicMock):

    async def __call__(self, *args, **kwargs):
        await MockDownlink.get_mock_downlink().receive_message()
        return super(MockReceiveMessage, self).__call__(*args, **kwargs)

    @staticmethod
    def set_call_count(call_count):
        MockDownlink.get_mock_downlink().call_counts_left = call_count

    @staticmethod
    def all_messages_has_been_sent():
        return MockDownlink.get_mock_downlink().all_messages_sent


class MockWebsocket:
    instance = None

    def __init__(self):
        self.connection = None
        self.closed = False
        self.sent_messages = list()
        self.messages_to_send = list()
        self.raise_exception = False
        self.custom_recv_func = None

    @staticmethod
    def get_mock_websocket():
        if MockWebsocket.instance is None:
            MockWebsocket.instance = MockWebsocket()

        return MockWebsocket.instance

    @staticmethod
    def clear():
        MockWebsocket.instance = None

    async def close(self):
        self.closed = True

    async def send(self, message):
        self.sent_messages.append(message)

    async def recv(self):

        if self.custom_recv_func is None:

            if self.raise_exception:
                raise Exception('WebSocket Exception!')

            message = self.messages_to_send.pop()

            if len(self.messages_to_send) == 0:
                self.connection.status = _ConnectionStatus.CLOSED

            return message

        else:
            return await self.custom_recv_func()


class ReceiveLoop:

    def __init__(self):
        self.call_count = 0

    async def recv_loop(self):
        while True:
            self.call_count = self.call_count + 1
            await asyncio.sleep(1)


class MockConnection:
    instance = None

    def __init__(self):
        self.owner = None
        self.messages_sent = list()
        self.messages_to_receive = list()

    @staticmethod
    def get_mock_connection():
        if MockConnection.instance is None:
            MockConnection.instance = MockConnection()

        return MockConnection.instance

    @staticmethod
    def clear():
        MockConnection.instance = None

    async def _wait_for_messages(self):
        while True:
            if len(self.messages_to_receive) > 0 and self.owner is not None:
                message = self.messages_to_receive.pop()
                await self.owner._receive_message(message)

            await asyncio.sleep(1)

    async def _send_message(self, message):
        self.messages_sent.append(message)


def mock_did_set_confirmation():
    print(1)
    pass


async def mock_did_set_callback(old, new):
    str(old)
    str(new)
    pass


async def mock_on_event_callback(event):
    str(event)
    pass


async def mock_did_update_callback(key, old, new):
    str(key)
    str(old)
    str(new)
    pass


async def mock_did_remove_callback(key, old):
    str(key)
    str(old)
    pass


def mock_exception_callback():
    print('Mock exception callback')


class MockExceptionOnce:
    instance = None

    def __init__(self):
        self.calls = 0
        self.actual_function = None

    @staticmethod
    def get_mock_exception_once():
        if MockExceptionOnce.instance is None:
            MockExceptionOnce.instance = MockExceptionOnce()

        return MockExceptionOnce.instance

    @staticmethod
    def clear():
        MockExceptionOnce.instance = None

    def side_effect(self, *args, **kwargs):
        if self.calls == 0:
            self.calls = self.calls + 1
            self.exception()
        else:
            return self.normal(*args, **kwargs)

    @staticmethod
    def exception():
        raise Exception('Mock exception')

    def normal(self, *args, **kwargs):
        return self.actual_function(*args, **kwargs)


class MockRunWithExceptionOnce(MagicMock):

    def __call__(self, *args, **kwargs):
        return super(MockRunWithExceptionOnce, self).__call__(*args, **kwargs)


class MockScheduleTask:
    instance = None

    def __init__(self):
        self.message = None
        self.call_count = 0

    @staticmethod
    async def async_execute(message):
        MockScheduleTask.instance.message = message
        MockScheduleTask.instance.call_count = MockScheduleTask.instance.call_count + 1

    @staticmethod
    def sync_execute(message):
        MockScheduleTask.instance.message = message
        MockScheduleTask.instance.call_count = MockScheduleTask.instance.call_count + 1

    @staticmethod
    async def async_exception_execute(message):
        MockScheduleTask.instance.message = message
        MockScheduleTask.instance.call_count = MockScheduleTask.instance.call_count + 1
        raise Exception('Mock async execute exception')

    @staticmethod
    async def async_infinite_cancel_execute():
        while True:
            await asyncio.sleep(1)

    @staticmethod
    def get_mock_schedule_task():
        if MockScheduleTask.instance is None:
            MockScheduleTask.instance = MockScheduleTask()

        return MockScheduleTask.instance

    @staticmethod
    def clear():
        MockScheduleTask.instance = None


class MockClass:

    def __init__(self):
        pass


class MockPerson:

    def __init__(self, name=None, age=None, friend=None):
        self.name = name
        self.age = age
        self.friend = friend


class MockPet:
    def __init__(self, name=None, age=None):
        self.name = name
        self.age = age


class MockCar:

    def __init__(self, make=None, model=None, year=None):
        self.make = make
        self.model = model
        self.year = year


def mock_func():
    return 'mock_func_response'


async def mock_coro():
    return 'mock_coro_response'


class MockExecuteOnException:
    instance = None

    def __init__(self):
        self.called = False

    def __call__(self, *args, **kwargs):
        self.called = True

    @staticmethod
    def get_mock_execute_on_exception():
        if MockExecuteOnException.instance is None:
            MockExecuteOnException.instance = MockExecuteOnException()

        return MockExecuteOnException.instance

    @staticmethod
    def clear():
        MockExecuteOnException.instance = None


class NewScope:
    class MockPerson:
        def __init__(self, name='Uriel'):
            self.name = name


class MockNoDefaultConstructor:

    def __init__(self, name):
        self.name = name


class MockModel:
    pass


class MockDownlinkManager:

    def __init__(self):
        self.called = 0
        self.event = None
        self.did_set_new = None
        self.did_set_old = None
        self.update_key = None
        self.update_value_new = None
        self.update_value_old = None
        self.remove_key = None
        self.remove_old_value = None
        self.strict = False
        self.registered_classes = dict()

    async def _subscribers_on_event(self, event):
        self.called = self.called + 1
        self.event = event

    async def _subscribers_did_set(self, did_set_new, did_set_old):
        self.called = self.called + 1
        self.did_set_new = did_set_new
        self.did_set_old = did_set_old

    async def _subscribers_did_update(self, update_key, update_value_new, update_value_old):
        self.called = self.called + 1
        self.update_key = update_key
        self.update_value_new = update_value_new
        self.update_value_old = update_value_old

    async def _subscribers_did_remove(self, remove_key, remove_old_value):
        self.called = self.called + 1
        self.remove_key = remove_key
        self.remove_old_value = remove_old_value


class MockEventCallback:

    def __init__(self):
        self.called = False
        self.event = None

    async def execute(self, event):
        self.called = True
        self.event = event


class MockDidSetCallback:
    def __init__(self):
        self.called = False
        self.new_value = None
        self.old_value = None

    async def execute(self, new_value, old_value):
        self.called = True
        self.new_value = new_value
        self.old_value = old_value


class MockDidUpdateCallback:
    def __init__(self):
        self.called = False
        self.key = None
        self.new_value = None
        self.old_value = None

    async def execute(self, key, new_value, old_value):
        self.called = True
        self.key = key
        self.new_value = new_value
        self.old_value = old_value


class MockDidRemoveCallback:
    def __init__(self):
        self.called = False
        self.key = None
        self.value = None

    async def execute(self, key, value):
        self.called = True
        self.key = key
        self.value = value
