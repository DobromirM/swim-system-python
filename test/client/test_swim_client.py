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
import aiounittest
from concurrent import futures
from threading import Thread
from unittest.mock import patch

from swimos.client._downlinks._downlinks import _ValueDownlinkView, _MapDownlinkView, _EventDownlinkView
from swimos.structures import Text
from test.utils import MockWebsocketConnect, MockWebsocket, MockAsyncFunction, MockScheduleTask, \
    mock_exception_callback, MockRunWithExceptionOnce, MockExceptionOnce
from swimos import SwimClient


class TestSwimClient(aiounittest.AsyncTestCase):

    def setUp(self):
        MockWebsocket.clear()
        MockScheduleTask.clear()
        MockExceptionOnce.clear()
        asyncio.get_event_loop().stop()
        asyncio.get_event_loop().close()

    def test_swim_client_start(self):
        # Given
        client = SwimClient()
        # When
        actual = client.start()
        # Then
        self.assertEqual(actual, client)
        self.assertIsInstance(actual._loop, asyncio.events.AbstractEventLoop)
        self.assertIsInstance(actual._loop_thread, Thread)
        self.assertFalse(actual._loop.is_closed())
        self.assertTrue(actual._loop_thread.is_alive())
        self.assertTrue(actual._has_started)
        client.stop()

    def test_swim_client_stop(self):
        # Given
        client = SwimClient()
        client.start()
        # When
        actual = client.stop()
        # Then
        self.assertEqual(client, actual)
        self.assertIsInstance(actual._loop, asyncio.events.AbstractEventLoop)
        self.assertIsInstance(actual._loop_thread, Thread)
        self.assertTrue(actual._loop.is_closed())
        self.assertFalse(actual._loop_thread.is_alive())
        self.assertFalse(actual._has_started)

    def test_swim_client_with_statement(self):
        # When
        with SwimClient() as swim_client:
            # Then
            self.assertIsInstance(swim_client, SwimClient)
            self.assertIsInstance(swim_client._loop, asyncio.events.AbstractEventLoop)
            self.assertIsInstance(swim_client._loop_thread, Thread)
            self.assertFalse(swim_client._loop.is_closed())
            self.assertTrue(swim_client._has_started)

        self.assertIsInstance(swim_client._loop, asyncio.events.AbstractEventLoop)
        self.assertIsInstance(swim_client._loop_thread, Thread)
        self.assertTrue(swim_client._loop.is_closed())
        self.assertFalse(swim_client._loop_thread.is_alive())
        self.assertFalse(swim_client._has_started)

    @patch('warnings.warn')
    @patch('traceback.print_tb')
    def test_swim_client_with_statement_exception_no_handler(self, mock_warn_tb, mock_warn):
        # When
        with SwimClient(debug=True) as swim_client:
            # Then
            self.assertIsInstance(swim_client, SwimClient)
            self.assertIsInstance(swim_client._loop, asyncio.events.AbstractEventLoop)
            self.assertIsInstance(swim_client._loop_thread, Thread)
            self.assertFalse(swim_client._loop.is_closed())
            self.assertTrue(swim_client._loop_thread.is_alive())

            swim_client.task_with_exception = lambda: (_ for _ in ()).throw(Exception,
                                                                            Exception('Mock exception in task'))

            swim_client.task_with_exception()

        mock_warn.assert_called_once()
        mock_warn_tb.assert_called_once()
        self.assertEqual('Mock exception in task', mock_warn.call_args_list[0][0][0])
        self.assertTrue(swim_client._loop.is_closed())
        self.assertFalse(swim_client._loop_thread.is_alive())

    @patch('warnings.warn')
    @patch('traceback.print_tb')
    @patch('os._exit')
    def test_swim_client_with_statement_exception_terminate(self, mock_exit, mock_warn_tb, mock_warn):
        # When
        with SwimClient(terminate_on_exception=True, debug=True) as swim_client:
            # Then
            self.assertIsInstance(swim_client, SwimClient)
            self.assertIsInstance(swim_client._loop, asyncio.events.AbstractEventLoop)
            self.assertFalse(swim_client._loop.is_closed())
            self.assertIsInstance(swim_client._loop_thread, Thread)
            self.assertTrue(swim_client._loop_thread.is_alive())

            swim_client.task_with_exception = lambda: (_ for _ in ()).throw(Exception,
                                                                            Exception('Mock exception in task'))

            swim_client.task_with_exception()

        self.assertTrue(swim_client._loop.is_closed())
        self.assertEqual('Mock exception in task', mock_warn.call_args_list[0][0][0])
        mock_warn_tb.assert_called_once()
        mock_warn.assert_called_once()
        mock_exit.assert_called_once_with(1)
        self.assertFalse(swim_client._loop_thread.is_alive())

    @patch('warnings.warn')
    @patch('traceback.print_tb')
    @patch('builtins.print')
    def test_swim_client_with_statement_exception_callback(self, mock_print, mock_warn_tb, mock_warn):
        # Given
        mock_callback = mock_exception_callback
        # When
        with SwimClient(execute_on_exception=mock_callback, debug=True) as swim_client:
            # Then
            self.assertIsInstance(swim_client._loop, asyncio.events.AbstractEventLoop)
            self.assertTrue(swim_client._loop_thread.is_alive())
            self.assertIsInstance(swim_client, SwimClient)
            self.assertFalse(swim_client._loop.is_closed())
            self.assertIsInstance(swim_client._loop_thread, Thread)

            swim_client.task_with_exception = lambda: (_ for _ in ()).throw(Exception,
                                                                            Exception('Mock exception in task'))

            swim_client.task_with_exception()

        self.assertEqual('Mock exception callback', mock_print.call_args_list[0][0][0])
        self.assertEqual('Mock exception in task', mock_warn.call_args_list[0][0][0])
        self.assertTrue(swim_client._loop.is_closed())
        mock_warn_tb.assert_called_once()
        self.assertFalse(swim_client._loop_thread.is_alive())

    @patch('warnings.warn')
    @patch('traceback.print_tb')
    @patch('os._exit')
    def test_swim_client_with_statement_exception_callback_and_terminate(self, mock_exit, mock_warn_tb, mock_warn):
        # Given
        mock_callback = mock_exception_callback
        # When
        with SwimClient(terminate_on_exception=True, execute_on_exception=mock_callback, debug=True) as swim_client:
            # Then
            self.assertIsInstance(swim_client, SwimClient)
            self.assertIsInstance(swim_client._loop, asyncio.events.AbstractEventLoop)
            self.assertFalse(swim_client._loop.is_closed())
            self.assertTrue(swim_client._loop_thread.is_alive())
            self.assertIsInstance(swim_client._loop_thread, Thread)

            swim_client.task_with_exception = lambda: (_ for _ in ()).throw(Exception,
                                                                            Exception('Mock exception in task'))

            swim_client.task_with_exception()

        mock_exit.assert_called_once_with(1)
        self.assertTrue(swim_client._loop.is_closed())
        self.assertEqual('Mock exception in task', mock_warn.call_args_list[0][0][0])
        mock_warn_tb.assert_called_once()
        mock_warn.assert_called_once()
        self.assertFalse(swim_client._loop_thread.is_alive())

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    def test_swim_client_command(self, mock_websocket_connect):
        # Given
        host_uri = 'ws://localhost:9001'
        node_uri = 'moo'
        lane_uri = 'cow'
        expected = '@command(node:moo,lane:cow)"Hello, World!"'
        with SwimClient() as swim_client:
            # When
            actual = swim_client.command(host_uri, node_uri, lane_uri, Text.create_from('Hello, World!'))
            while not actual.done():
                pass

        # Then
        self.assertIsInstance(actual, futures.Future)
        mock_websocket_connect.assert_called_once_with(host_uri)
        self.assertEqual(expected, MockWebsocket.get_mock_websocket().sent_messages[0])

    def test_swim_client_command_before_open(self):
        # Given
        swim_client = SwimClient()
        # When
        downlink_event = swim_client.downlink_event()
        # Then
        self.assertIsInstance(downlink_event, _EventDownlinkView)
        self.assertEqual(downlink_event._client, swim_client)

    def test_swim_client_downlink_event(self):
        # Given
        with SwimClient() as swim_client:
            # When
            downlink_event = swim_client.downlink_event()

        # Then
        self.assertIsInstance(downlink_event, _EventDownlinkView)
        self.assertEqual(downlink_event._client, swim_client)

    @patch('warnings.warn')
    def test_swim_client_downlink_event_open_before_client_started(self, mock_warn):
        # Given
        swim_client = SwimClient()
        # When
        downlink_event = swim_client.downlink_event()
        downlink_event.open()
        # Then
        self.assertEqual('Cannot execute "_add_downlink_view" before the client has been started!',
                         mock_warn.call_args_list[0][0][0])

    def test_swim_client_downlink_map(self):
        # Given
        with SwimClient() as swim_client:
            # When
            downlink_map = swim_client.downlink_map()

        # Then
        self.assertIsInstance(downlink_map, _MapDownlinkView)
        self.assertEqual(downlink_map._client, swim_client)

    @patch('warnings.warn')
    def test_swim_client_downlink_map_open_before_client_started(self, mock_warn):
        # Given
        swim_client = SwimClient()
        # When
        downlink_map = swim_client.downlink_map()
        downlink_map.open()
        # Then
        self.assertEqual('Cannot execute "_add_downlink_view" before the client has been started!',
                         mock_warn.call_args_list[0][0][0])

    def test_swim_client_downlink_value(self):
        # Given
        with SwimClient() as swim_client:
            # When
            downlink_view = swim_client.downlink_value()

        # Then
        self.assertIsInstance(downlink_view, _ValueDownlinkView)
        self.assertEqual(downlink_view._client, swim_client)

    @patch('warnings.warn')
    def test_swim_client_downlink_value_open_before_client_started(self, mock_warn):
        # Given
        swim_client = SwimClient()
        # When
        downlink_value = swim_client.downlink_value()
        downlink_value.open()
        # Then
        self.assertEqual('Cannot execute "_add_downlink_view" before the client has been started!',
                         mock_warn.call_args_list[0][0][0])

    @patch('swimos.client._connections._ConnectionPool._add_downlink_view', new_callable=MockAsyncFunction)
    async def test_swim_client_add_downlink_view(self, mock_add_downlink):
        # Given
        host_uri = 'ws://localhost:9001'
        node_uri = 'moo'
        lane_uri = 'cow'

        MockWebsocket.get_mock_websocket().messages_to_send.append('@synced(node:"moo",lane:"cow")')

        with SwimClient() as swim_client:
            downlink_view = swim_client.downlink_value()
            downlink_view._host_uri = host_uri
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            # When
            await swim_client._add_downlink_view(downlink_view)

        # Then
        mock_add_downlink.assert_called_once_with(downlink_view)

    @patch('swimos.client._connections._ConnectionPool._add_downlink_view', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._ConnectionPool._remove_downlink_view', new_callable=MockAsyncFunction)
    async def test_swim_client_remove_downlink_view(self, mock_remove_downlink, mock_add_downlink):
        # Given
        host_uri = 'ws://localhost:9001'
        node_uri = 'moo'
        lane_uri = 'cow'

        MockWebsocket.get_mock_websocket().messages_to_send.append('@synced(node:"moo",lane:"cow")')

        with SwimClient() as swim_client:
            downlink_view = swim_client.downlink_value()
            downlink_view._host_uri = host_uri
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            await swim_client._add_downlink_view(downlink_view)
            # When
            await swim_client._remove_downlink_view(downlink_view)

        # Then
        mock_add_downlink.assert_called_once_with(downlink_view)
        mock_remove_downlink.assert_called_once_with(downlink_view)

    @patch('swimos.client._connections._ConnectionPool._get_connection', new_callable=MockAsyncFunction)
    async def test_swim_client_get_connection(self, mock_get_connection):
        # Given
        host_uri = 'ws://localhost:9001'
        scheme = 'ws'
        node_uri = 'moo'
        lane_uri = 'cow'

        MockWebsocket.get_mock_websocket().messages_to_send.append('@synced(node:"moo",lane:"cow")')

        with SwimClient() as swim_client:
            downlink_view = swim_client.downlink_value()
            downlink_view._host_uri = host_uri
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            # When
            await swim_client._get_connection(host_uri, scheme)

        # Then
        mock_get_connection.assert_called_once_with(host_uri, scheme)

    async def test_swim_client_test_schedule_task(self):
        #  Given
        mock_task = MockScheduleTask.get_mock_schedule_task()
        with SwimClient() as swim_client:
            # When
            actual = swim_client._schedule_task(mock_task.async_execute, 'foo')
            while not actual.done():
                pass

        # Then
        self.assertEqual(1, mock_task.call_count)
        self.assertEqual('foo', mock_task.message)
        self.assertIsInstance(actual, futures.Future)

    @patch('warnings.warn')
    @patch('traceback.print_tb')
    def test_swim_client_test_schedule_task_exception(self, mock_print_tb, mock_warn):
        # Given
        mock_task = MockScheduleTask.get_mock_schedule_task()
        original_run = asyncio.run_coroutine_threadsafe

        with patch('asyncio.run_coroutine_threadsafe', new_callable=MockRunWithExceptionOnce) as mock_run:
            mock_exception_once = MockExceptionOnce.get_mock_exception_once()
            mock_exception_once.actual_function = original_run
            mock_run.side_effect = mock_exception_once.side_effect

            # When
            with SwimClient() as swim_client:
                actual = swim_client._schedule_task(mock_task.sync_execute, 'foo')

            self.assertEqual('Mock exception', mock_warn.call_args_list[0][0][0])
            mock_print_tb.assert_not_called()
            self.assertIsNone(actual)
            self.assertEqual(2, mock_run.call_count)

    @patch('warnings.warn')
    @patch('traceback.print_tb')
    def test_swim_client_test_schedule_task_exception_debug(self, mock_print_tb, mock_warn):
        # Given
        mock_task = MockScheduleTask.get_mock_schedule_task()
        original_run = asyncio.run_coroutine_threadsafe

        with patch('asyncio.run_coroutine_threadsafe', new_callable=MockRunWithExceptionOnce) as mock_run:
            mock_exception_once = MockExceptionOnce.get_mock_exception_once()
            mock_exception_once.actual_function = original_run
            mock_run.side_effect = mock_exception_once.side_effect

            # When
            with SwimClient(debug=True) as swim_client:
                actual = swim_client._schedule_task(mock_task.sync_execute, 'foo')

            self.assertEqual('Mock exception', mock_warn.call_args_list[0][0][0])
            mock_print_tb.assert_called_once()
            self.assertIsNone(actual)

    @patch('warnings.warn')
    @patch('traceback.print_tb')
    def test_swim_client_test_schedule_task_that_raises_exception(self, mock_warn_tb, mock_warn):
        # Given
        mock_task = MockScheduleTask.get_mock_schedule_task()
        with SwimClient(debug=True) as swim_client:
            # When
            actual = swim_client._schedule_task(mock_task.async_exception_execute, 'foo')
            while not actual.done():
                pass

        # Then
        mock_warn_tb.assert_called_once()
        mock_warn.assert_called_once()
        self.assertEqual('Mock async execute exception', mock_warn.call_args_list[0][0][0])
        self.assertEqual(1, mock_task.call_count)
        self.assertEqual('foo', mock_task.message)
        self.assertIsInstance(actual, futures.Future)

    def test_swim_client_test_schedule_task_that_is_cancelled(self):
        # Given
        mock_task = MockScheduleTask.get_mock_schedule_task()
        with SwimClient() as swim_client:
            # When
            actual = swim_client._schedule_task(mock_task.async_infinite_cancel_execute)
        # Then
        self.assertIsInstance(actual, futures.Future)
        self.assertTrue(actual.cancelled())
