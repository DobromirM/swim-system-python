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
import aiounittest

from unittest.mock import patch
from swimos import SwimClient
from swimos.client._connections import _WSConnection, _ConnectionStatus, _ConnectionPool, _DownlinkManagerPool, \
    _DownlinkManager, _DownlinkManagerStatus
from swimos.client._downlinks._downlinks import _ValueDownlinkModel
from swimos.structures import Text, Value
from swimos.warp._warp import _SyncedResponse, _LinkedResponse, _EventMessage
from test.utils import MockWebsocket, MockWebsocketConnect, MockAsyncFunction, MockReceiveMessage, MockConnection, \
    MockDownlink, mock_did_set_callback, MockClass, mock_on_event_callback, mock_did_update_callback, \
    mock_did_remove_callback, MockWebsocketConnectException


class TestConnections(aiounittest.AsyncTestCase):

    def setUp(self):
        MockWebsocket.clear()
        MockDownlink.clear()
        MockConnection.clear()

    def test_connection_pool(self):
        # When
        actual = _ConnectionPool()
        # Then
        self.assertEqual(0, actual._size)

    async def test_pool_get_connection_new(self):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        scheme = 'ws'
        # When
        actual = await pool._get_connection(uri, scheme)
        # Then
        self.assertEqual(uri, actual.host_uri)
        self.assertEqual(None, actual.websocket)
        self.assertEqual(_ConnectionStatus.CLOSED, actual.status)
        self.assertEqual(1, pool._size)

    async def test_pool_get_connection_existing(self):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        scheme = 'ws'
        expected = await pool._get_connection(uri, scheme)
        expected.status = _ConnectionStatus.IDLE
        # When
        actual = await pool._get_connection(uri, scheme)
        # Then
        self.assertEqual(expected, actual)
        self.assertEqual(1, pool._size)

    async def test_pool_get_connection_closed(self):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        scheme = 'ws'
        expected = await pool._get_connection(uri, scheme)
        # When
        actual = await pool._get_connection(uri, scheme)
        # Then
        self.assertNotEqual(expected, actual)
        self.assertEqual(uri, actual.host_uri)
        self.assertEqual(None, actual.websocket)
        self.assertEqual(_ConnectionStatus.CLOSED, actual.status)
        self.assertEqual(1, pool._size)

    async def test_pool_remove_connection_existing(self):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        scheme = 'ws'
        connection = await pool._get_connection(uri, scheme)
        connection.status = _ConnectionStatus.IDLE
        # When
        await pool._remove_connection(uri)
        # Then
        self.assertEqual(0, pool._size)
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)

    async def test_pool_remove_connection_non_existing(self):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        # When
        await pool._remove_connection(uri)
        # Then
        self.assertEqual(0, pool._size)

    @patch('swimos.client._connections._WSConnection._subscribe', new_callable=MockAsyncFunction)
    async def test_pool_add_downlink_view_existing_connection(self, mock_subscribe):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        scheme = 'ws'
        connection = await pool._get_connection(uri, scheme)
        connection.status = _ConnectionStatus.IDLE
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(uri)
        # When
        await pool._add_downlink_view(downlink_view)
        # Then
        self.assertEqual(uri, downlink_view._host_uri)
        self.assertEqual(1, pool._size)
        self.assertEqual(uri, connection.host_uri)
        self.assertEqual(connection, downlink_view._connection)
        self.assertEqual(_ConnectionStatus.IDLE, connection.status)
        mock_subscribe.assert_called_once_with(downlink_view)

    @patch('swimos.client._connections._WSConnection._subscribe', new_callable=MockAsyncFunction)
    async def test_pool_add_downlink_view_non_existing_connection(self, mock_subscribe):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(uri)
        # When
        await pool._add_downlink_view(downlink_view)
        # Then
        self.assertEqual(uri, downlink_view._host_uri)
        self.assertEqual(1, pool._size)
        mock_subscribe.assert_called_once_with(downlink_view)

    @patch('swimos.client._connections._WSConnection._subscribe', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._WSConnection._unsubscribe', new_callable=MockAsyncFunction)
    async def test_pool_remove_downlink_view_existing_connection_open(self, mock_unsubscribe, mock_subscribed):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(uri)
        await pool._add_downlink_view(downlink_view)
        downlink_view._connection.status = _ConnectionStatus.IDLE
        # When
        await pool._remove_downlink_view(downlink_view)
        # Then
        pass
        self.assertEqual(1, pool._size)
        self.assertEqual(_ConnectionStatus.IDLE, downlink_view._connection.status)
        mock_subscribed.assert_called_with(downlink_view)
        mock_unsubscribe.assert_called_with(downlink_view)

    @patch('swimos.client._connections._WSConnection._subscribe', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._WSConnection._unsubscribe', new_callable=MockAsyncFunction)
    async def test_pool_remove_downlink_view_existing_connection_closed(self, mock_unsubscribe, mock_subscribe):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        scheme = 'ws'
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(uri)
        await pool._add_downlink_view(downlink_view)
        connection = pool._get_connection(uri, scheme)
        connection.close()
        # When
        await pool._remove_downlink_view(downlink_view)
        # Then
        pass
        self.assertEqual(0, pool._size)
        self.assertEqual(_ConnectionStatus.CLOSED, downlink_view._connection.status)
        mock_subscribe.assert_called_once_with(downlink_view)
        mock_unsubscribe.assert_called_once_with(downlink_view)

    @patch('swimos.client._connections._DownlinkManagerPool._deregister_downlink_view', new_callable=MockAsyncFunction)
    async def test_pool_remove_downlink_view_non_existing_connection(self, mock_deregister_downlink_view):
        # Given
        pool = _ConnectionPool()
        uri = 'ws://foo_bar:9000'
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(uri)
        await pool._remove_connection(uri)
        # When
        await pool._remove_downlink_view(downlink_view)
        # Then
        pass
        self.assertEqual(0, pool._size)
        mock_deregister_downlink_view.assert_not_called()

    async def test_ws_connection(self):
        # Given
        host_uri = 'ws://localhost:9001'
        scheme = 'ws'
        # When
        actual = _WSConnection(host_uri, scheme)
        # Then
        self.assertEqual(host_uri, actual.host_uri)
        self.assertIsNone(actual.websocket)
        self.assertEqual(_ConnectionStatus.CLOSED, actual.status)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    @patch('swimos.client._connections._DownlinkManager._add_view', new_callable=MockAsyncFunction)
    async def test_ws_connection_subscribe_single(self, mock_add_view, mock_websocket):
        # Given
        host_uri = 'ws://localhost:9001'
        scheme = 'ws'
        actual = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(host_uri)
        downlink_view.set_node_uri('bar')
        downlink_view.set_lane_uri('baz')
        # When
        await actual._subscribe(downlink_view)
        # Then
        self.assertEqual(host_uri, actual.host_uri)
        self.assertEqual(MockWebsocket.get_mock_websocket(), actual.websocket)
        self.assertEqual(_ConnectionStatus.IDLE, actual.status)
        self.assertTrue(actual._has_subscribers())
        mock_websocket.assert_called_once_with(host_uri)
        mock_add_view.assert_called_once_with(downlink_view)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    @patch('swimos.client._connections._DownlinkManager._add_view', new_callable=MockAsyncFunction)
    async def test_ws_connection_subscribe_multiple(self, mock_add_view, mock_websocket):
        # Given
        host_uri = 'ws://1.1.1.1:9001'
        scheme = 'ws'
        actual = _WSConnection(host_uri, scheme)

        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_host_uri(host_uri)
        first_downlink_view.set_node_uri('bar')
        first_downlink_view.set_lane_uri('baz')

        second_downlink_view = client.downlink_value()
        second_downlink_view.set_host_uri(host_uri)
        second_downlink_view.set_node_uri('foo')
        second_downlink_view.set_lane_uri('bar')
        # When
        await actual._subscribe(first_downlink_view)
        await actual._subscribe(second_downlink_view)
        # Then
        self.assertEqual(host_uri, actual.host_uri)
        self.assertEqual(MockWebsocket.get_mock_websocket(), actual.websocket)
        self.assertEqual(_ConnectionStatus.IDLE, actual.status)
        self.assertTrue(actual._has_subscribers())
        mock_websocket.assert_called_once_with('ws://1.1.1.1:9001')
        mock_add_view.assert_any_call(first_downlink_view)
        mock_add_view.assert_any_call(second_downlink_view)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    @patch('swimos.client._connections._DownlinkManager._add_view', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._remove_view', new_callable=MockAsyncFunction)
    async def test_ws_connection_unsubscribe_all(self, mock_remove_view, mock_add_view, mock_websocket):
        # Given
        host_uri = 'ws://0.0.0.0:9001'
        scheme = 'ws'
        actual = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(host_uri)
        downlink_view.set_node_uri('foo')
        downlink_view.set_lane_uri('bar')

        await actual._subscribe(downlink_view)
        # When
        await actual._unsubscribe(downlink_view)
        # Then
        self.assertEqual(host_uri, actual.host_uri)
        self.assertEqual(MockWebsocket.get_mock_websocket(), actual.websocket)
        self.assertEqual(_ConnectionStatus.CLOSED, actual.status)
        self.assertFalse(actual._has_subscribers())
        mock_websocket.assert_called_once_with('ws://0.0.0.0:9001')
        self.assertTrue(actual.websocket.closed)
        mock_add_view.assert_called_once_with(downlink_view)
        mock_remove_view.assert_called_once_with(downlink_view)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    @patch('swimos.client._connections._DownlinkManager._add_view', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._remove_view', new_callable=MockAsyncFunction)
    async def test_ws_connection_unsubscribe_one(self, mock_remove_view, mock_add_view, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        actual = _WSConnection(host_uri, scheme)

        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_host_uri(host_uri)
        first_downlink_view.set_node_uri('foo')
        first_downlink_view.set_lane_uri('bar')

        second_downlink_view = client.downlink_value()
        second_downlink_view.set_host_uri(host_uri)
        second_downlink_view.set_node_uri('bar')
        second_downlink_view.set_lane_uri('baz')

        await actual._subscribe(first_downlink_view)
        await actual._subscribe(second_downlink_view)
        # When
        await actual._unsubscribe(first_downlink_view)
        # Then
        self.assertEqual(host_uri, actual.host_uri)
        self.assertEqual(MockWebsocket.get_mock_websocket(), actual.websocket)
        self.assertEqual(_ConnectionStatus.IDLE, actual.status)
        self.assertTrue(actual._has_subscribers())
        mock_websocket.assert_called_once_with('ws://1.2.3.4:9001')
        self.assertFalse(actual.websocket.closed)
        mock_add_view.assert_any_call(first_downlink_view)
        mock_add_view.assert_any_call(second_downlink_view)
        mock_remove_view.assert_called_once_with(first_downlink_view)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_open_new(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        # When
        await connection._open()
        # Then
        self.assertEqual(_ConnectionStatus.IDLE, connection.status)
        mock_websocket.assert_called_once_with(host_uri)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_wss_connection_open_new(self, mock_websocket):
        # Given
        host_uri = 'wss://1.2.3.4:9001'
        scheme = 'wss'
        connection = _WSConnection(host_uri, scheme)
        # When
        await connection._open()
        # Then
        self.assertEqual(_ConnectionStatus.IDLE, connection.status)
        mock_websocket.assert_called_once_with(host_uri, ssl=True)

    @patch('websockets.connect', new_callable=MockWebsocketConnectException)
    async def test_ws_connection_open_error(self, mock_websocket):
        # Given
        MockWebsocket.get_mock_websocket().raise_exception = True
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        # When
        with self.assertRaises(Exception) as error:
            # noinspection PyTypeChecker
            await connection._open()
        # Then
        message = error.exception.args[0]
        self.assertEqual(message, 'Mock_websocket_connect_exception')
        mock_websocket.assert_called_once_with(host_uri)
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)

    @patch('websockets.connect', new_callable=MockWebsocketConnectException)
    async def test_wss_connection_open_error(self, mock_websocket):
        # Given
        MockWebsocket.get_mock_websocket().raise_exception = True
        host_uri = 'wss://1.2.3.4:9001'
        scheme = 'wss'
        connection = _WSConnection(host_uri, scheme)
        # When
        with self.assertRaises(Exception) as error:
            # noinspection PyTypeChecker
            await connection._open()
        # Then
        message = error.exception.args[0]
        self.assertEqual(message, 'Mock_websocket_connect_exception')
        mock_websocket.assert_called_once_with(host_uri, ssl=True)
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_open_already_opened(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        await connection._open()
        # When
        await connection._open()
        # Then
        self.assertEqual(_ConnectionStatus.IDLE, connection.status)
        mock_websocket.assert_called_once_with(host_uri)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_close_opened(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        await connection._open()
        # When
        await connection._close()
        # Then
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)
        mock_websocket.assert_called_once_with(host_uri)
        self.assertTrue(connection.websocket.closed)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_close_missing_websocket(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        # When
        await connection._close()
        # Then
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)
        mock_websocket.assert_not_called()
        self.assertIsNone(connection.websocket)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_close_already_closed(self, mock_websocket):
        # Given
        host_uri = 'ws://5.5.5.5:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        await connection._open()
        await connection._close()
        # When
        await connection._close()
        # Then
        mock_websocket.assert_called_once_with(host_uri)
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)
        self.assertTrue(connection.websocket.closed)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_send_message_existing_websocket_single(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        message = 'Hello, World'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        await connection._open()
        # When
        await connection._send_message(message)
        # Then
        mock_websocket.assert_called_once_with(host_uri)
        self.assertEqual(message, connection.websocket.sent_messages[0])

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_send_message_existing_websocket_multiple(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        first_message = 'Hello, World'
        second_message = 'Hello, Friend'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        await connection._open()
        # When
        await connection._send_message(first_message)
        await connection._send_message(second_message)
        # Then
        mock_websocket.assert_called_once_with(host_uri)
        self.assertEqual(first_message, connection.websocket.sent_messages[0])
        self.assertEqual(second_message, connection.websocket.sent_messages[1])

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_send_message_non_existing_websocket(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        message = 'Hello, World'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        # When
        await connection._send_message(message)
        # Then
        mock_websocket.assert_called_once_with(host_uri)
        self.assertEqual(message, connection.websocket.sent_messages[0])

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_ws_connection_send_message_closed(self, mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        message = 'Hello, World'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        await connection._open()
        await connection._close()
        # When
        await connection._send_message(message)
        # Then
        self.assertEqual(2, mock_websocket.call_count)
        mock_websocket.assert_called_with(host_uri)
        self.assertEqual(message, connection.websocket.sent_messages[0])

    async def test_ws_connection_wait_for_message_closed(self):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        # When
        await connection._wait_for_messages()
        # Then
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    @patch('swimos.client._connections._DownlinkManager._add_view', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._receive_message', new_callable=MockAsyncFunction)
    async def test_ws_connection_wait_for_message_receive_single(self, mock_receive_message, mock_add_view,
                                                                 mock_websocket):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        MockWebsocket.get_mock_websocket().connection = connection

        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(host_uri)
        downlink_view.set_node_uri('foo')
        downlink_view.set_lane_uri('bar')
        await connection._subscribe(downlink_view)

        expected = '@sync(node:foo,lane:bar)'
        connection.websocket.messages_to_send.append(expected)
        # When
        await connection._wait_for_messages()
        # Then
        actual = mock_receive_message.call_args[0][0]._to_recon()
        self.assertEqual(expected, actual)
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)
        mock_add_view.assert_called_once_with(downlink_view)
        mock_websocket.assert_called_once_with(host_uri)
        mock_receive_message.assert_called_once()

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    @patch('swimos.client._connections._DownlinkManager._add_view', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._receive_message', new_callable=MockReceiveMessage)
    async def test_ws_connection_wait_for_message_receive_multiple(self, mock_receive_message, mock_add_view,
                                                                   mock_websocket):
        # Given
        host_uri = 'ws://2.2.2.2:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        MockWebsocket.get_mock_websocket().connection = connection
        mock_receive_message.set_call_count(3)

        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(host_uri)
        downlink_view.set_node_uri('baz')
        downlink_view.set_lane_uri('qux')
        await connection._subscribe(downlink_view)

        first_message = '@synced(node:baz,lane:qux)'
        second_message = '@linked(node:baz,lane:qux)'
        third_message = '@synced(node:baz,lane:qux)'

        expected = {first_message, second_message, third_message}
        connection.websocket.messages_to_send.append(first_message)
        connection.websocket.messages_to_send.append(second_message)
        connection.websocket.messages_to_send.append(third_message)
        # When
        await connection._wait_for_messages()
        await mock_receive_message.all_messages_has_been_sent().wait()
        # Then
        messages = mock_receive_message.call_args_list
        first_actual_message = messages[0][0][0]._to_recon()
        second_actual_message = messages[1][0][0]._to_recon()
        third_actual_message = messages[2][0][0]._to_recon()
        actual = {first_actual_message, second_actual_message, third_actual_message}
        self.assertEqual(expected, actual)
        self.assertEqual(_ConnectionStatus.CLOSED, connection.status)
        mock_add_view.assert_called_once_with(downlink_view)
        mock_websocket.assert_called_once_with(host_uri)
        self.assertEqual(3, mock_receive_message.call_count)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    @patch('swimos.client._connections._DownlinkManager._add_view', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._receive_message', new_callable=MockReceiveMessage)
    async def test_ws_connection_wait_for_message_receive_exception(self, mock_receive_message, mock_add_view,
                                                                    mock_websocket):
        # Given
        host_uri = 'ws://5.5.5.5:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        MockWebsocket.get_mock_websocket().connection = connection
        mock_websocket.set_raise_exception(True)

        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_host_uri(host_uri)
        downlink_view.set_node_uri('boo')
        downlink_view.set_lane_uri('far')
        await connection._subscribe(downlink_view)
        # When
        with self.assertRaises(Exception) as error:
            await connection._wait_for_messages()
        # Then
        message = error.exception.args[0]
        self.assertEqual('WebSocket Exception!', message)
        mock_receive_message.assert_not_called()
        mock_websocket.assert_called_once()
        mock_add_view.assert_called_once_with(downlink_view)

    async def test_downlink_manager_pool(self):
        # When
        actual = _DownlinkManagerPool()
        # Then
        self.assertIsInstance(actual, _DownlinkManagerPool)
        self.assertEqual(0, actual._size)

    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_register_downlink_view_single(self, mock_open):
        # Given
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('boo')
        downlink_view.set_lane_uri('far')
        actual = _DownlinkManagerPool()
        # When
        await actual._register_downlink_view(downlink_view)
        # Then
        self.assertEqual(1, actual._size)
        mock_open.assert_called_once()

    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_register_downlink_view_multiple_different_routes(self, mock_open):
        # Given
        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_node_uri('boo')
        first_downlink_view.set_lane_uri('far')
        second_downlink_view = client.downlink_value()
        second_downlink_view.set_node_uri('poo')
        second_downlink_view.set_lane_uri('par')
        actual = _DownlinkManagerPool()
        # When
        await actual._register_downlink_view(first_downlink_view)
        await actual._register_downlink_view(second_downlink_view)
        # Then
        self.assertEqual(2, actual._size)
        self.assertEqual(2, mock_open.call_count)

    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_register_downlink_view_multiple_same_route(self, mock_open):
        # Given
        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_node_uri('boo')
        first_downlink_view.set_lane_uri('far')
        second_downlink_view = client.downlink_value()
        second_downlink_view.set_node_uri('boo')
        second_downlink_view.set_lane_uri('far')
        actual = _DownlinkManagerPool()
        # When
        await actual._register_downlink_view(first_downlink_view)
        await actual._register_downlink_view(second_downlink_view)
        # Then
        self.assertEqual(1, actual._size)
        mock_open.assert_called_once()

    @patch('swimos.client._connections._DownlinkManager._close', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_deregister_downlink_view_single_existing(self, mock_open, mock_close):
        # Given
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('moo')
        downlink_view.set_lane_uri('cow')
        actual = _DownlinkManagerPool()
        await actual._register_downlink_view(downlink_view)
        # When
        await actual._deregister_downlink_view(downlink_view)
        # Then
        self.assertEqual(0, actual._size)
        mock_open.assert_called_once()
        mock_close.assert_called_once()

    @patch('swimos.client._connections._DownlinkManager._close', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_deregister_downlink_view_single_non_existing(self, mock_close):
        # Given
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('foo')
        downlink_view.set_lane_uri('bar')
        actual = _DownlinkManagerPool()
        # When
        await actual._deregister_downlink_view(downlink_view)
        # Then
        self.assertEqual(0, actual._size)
        mock_close.assert_not_called()

    @patch('swimos.client._connections._DownlinkManager._close', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_deregister_downlink_view_multiple_same_route(self, mock_open, mock_close):
        # Given
        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_node_uri('qux')
        first_downlink_view.set_lane_uri('baz')
        second_downlink_view = client.downlink_value()
        second_downlink_view.set_node_uri('qux')
        second_downlink_view.set_lane_uri('baz')
        actual = _DownlinkManagerPool()
        await actual._register_downlink_view(first_downlink_view)
        await actual._register_downlink_view(second_downlink_view)
        # When
        await actual._deregister_downlink_view(first_downlink_view)
        await actual._deregister_downlink_view(second_downlink_view)
        # Then
        self.assertEqual(0, actual._size)
        self.assertEqual(1, mock_open.call_count)
        self.assertEqual(1, mock_close.call_count)

    @patch('swimos.client._connections._DownlinkManager._close', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_deregister_downlink_view_multiple_different_routes(self, mock_open,
                                                                                            mock_close):
        # Given
        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_node_uri('parrot')
        first_downlink_view.set_lane_uri('dead')
        second_downlink_view = client.downlink_value()
        second_downlink_view.set_node_uri('ghost')
        second_downlink_view.set_lane_uri('boo')
        actual = _DownlinkManagerPool()
        await actual._register_downlink_view(first_downlink_view)
        await actual._register_downlink_view(second_downlink_view)
        # When
        await actual._deregister_downlink_view(first_downlink_view)
        await actual._deregister_downlink_view(second_downlink_view)
        # Then
        self.assertEqual(0, actual._size)
        self.assertEqual(2, mock_open.call_count)
        self.assertEqual(2, mock_close.call_count)

    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._receive_message', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_receive_message_existing_route(self, mock_receive_message, mock_open):
        # Given
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('moo')
        downlink_view.set_lane_uri('cow')
        actual = _DownlinkManagerPool()
        await actual._register_downlink_view(downlink_view)
        message = _SyncedResponse('moo', 'cow')
        # When
        await actual._receive_message(message)
        # Then
        mock_open.assert_called_once()
        mock_receive_message.assert_called_once_with(message)

    @patch('swimos.client._connections._DownlinkManager._open', new_callable=MockAsyncFunction)
    @patch('swimos.client._connections._DownlinkManager._receive_message', new_callable=MockAsyncFunction)
    async def test_downlink_manager_pool_receive_message_non_existing_route(self, mock_receive_message, mock_open):
        # Given
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('moo')
        downlink_view.set_lane_uri('cow')
        actual = _DownlinkManagerPool()
        await actual._register_downlink_view(downlink_view)
        message = _SyncedResponse('poo', 'pow')
        # When
        await actual._receive_message(message)
        # Then
        mock_open.assert_called_once()
        mock_receive_message.assert_not_called()

    async def test_downlink_manager(self):
        # Given
        host_uri = 'ws://5.5.5.5:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        # When
        actual = _DownlinkManager(connection)
        # Then
        self.assertIsInstance(actual, _DownlinkManager)
        self.assertIsNone(actual.downlink_model)
        self.assertEqual(connection, actual.connection)
        self.assertEqual(0, actual._view_count)
        self.assertEqual(_DownlinkManagerStatus.CLOSED, actual.status)

    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_open_new(self, mock_schedule_task):
        # Given
        host_uri = 'ws://5.5.5.5:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('foo')
        downlink_view.set_lane_uri('bar')
        actual = _DownlinkManager(connection)
        downlink_model = await downlink_view._create_downlink_model(actual)
        downlink_model.connection = MockConnection.get_mock_connection()
        actual.downlink_model = downlink_model
        # When
        await actual._open()
        # Then
        self.assertEqual(_DownlinkManagerStatus.OPEN, actual.status)
        mock_schedule_task.assert_called_once_with(MockConnection.get_mock_connection()._wait_for_messages)
        self.assertEqual(1, len(MockConnection.get_mock_connection().messages_sent))
        self.assertEqual('@sync(node:foo,lane:bar)', MockConnection.get_mock_connection().messages_sent[0])

    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_open_existing(self, mock_schedule_task):
        # Given
        host_uri = 'ws://5.5.5.5:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('moo')
        downlink_view.set_lane_uri('car')
        actual = _DownlinkManager(connection)
        downlink_model = await downlink_view._create_downlink_model(actual)
        downlink_model.connection = MockConnection.get_mock_connection()
        actual.downlink_model = downlink_model
        await actual._open()
        # When
        await actual._open()
        # Then
        self.assertEqual(_DownlinkManagerStatus.OPEN, actual.status)
        self.assertEqual('@sync(node:moo,lane:car)', MockConnection.get_mock_connection().messages_sent[0])
        self.assertEqual(1, len(MockConnection.get_mock_connection().messages_sent))
        mock_schedule_task.assert_called_once_with(MockConnection.get_mock_connection()._wait_for_messages)

    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_close_running(self, mock_schedule_task):
        # Given
        host_uri = 'ws://1.2.3.4:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('moo')
        downlink_view.set_lane_uri('car')
        actual = _DownlinkManager(connection)
        downlink_model = await downlink_view._create_downlink_model(actual)
        downlink_model.connection = MockConnection.get_mock_connection()
        actual.downlink_model = downlink_model
        await actual._open()
        # When
        await actual._close()
        # Then
        self.assertEqual(_DownlinkManagerStatus.CLOSED, actual.status)
        self.assertEqual(1, len(MockConnection.get_mock_connection().messages_sent))
        self.assertEqual(2, mock_schedule_task.call_count)

    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_close_stopped(self, mock_schedule_task):
        # Given
        host_uri = 'ws://4.3.2.1:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('boo')
        downlink_view.set_lane_uri('far')
        actual = _DownlinkManager(connection)
        downlink_model = await downlink_view._create_downlink_model(actual)
        downlink_model.connection = MockConnection.get_mock_connection()
        await actual._init_downlink_model(downlink_view)
        # When
        await actual._close()
        # Then
        self.assertEqual(_DownlinkManagerStatus.CLOSED, actual.status)
        self.assertEqual(0, len(MockConnection.get_mock_connection().messages_sent))
        self.assertEqual(0, mock_schedule_task.call_count)

    async def test_downlink_manager_init_downlink_model(self):
        # Given
        host_uri = 'ws://100.100.100.100:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('bar')
        downlink_view.set_lane_uri('baz')
        actual = _DownlinkManager(connection)
        # When
        await actual._init_downlink_model(downlink_view)
        # Then
        self.assertEqual(downlink_view._lane_uri, actual.downlink_model.lane_uri)
        self.assertIsInstance(actual.downlink_model, _ValueDownlinkModel)
        self.assertEqual(_DownlinkManagerStatus.CLOSED, actual.status)
        self.assertEqual(downlink_view._client, actual.downlink_model.client)
        self.assertEqual(downlink_view._node_uri, actual.downlink_model.node_uri)
        self.assertEqual(downlink_view._host_uri, actual.downlink_model.host_uri)
        self.assertEqual(actual, actual.downlink_model.downlink_manager)
        self.assertEqual(actual.connection, actual.downlink_model.connection)
        self.assertEqual(actual.downlink_model.downlink_manager, actual)
        self.assertFalse(actual.strict)

    async def test_downlink_manager_init_downlink_model_strict_classes(self):
        # Given
        host_uri = 'ws://100.100.100.100:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client.start()
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('boo')
        downlink_view.set_lane_uri('moo')
        downlink_view.strict = True
        downlink_view.register_class(MockClass)
        actual = _DownlinkManager(connection)
        # When
        await actual._init_downlink_model(downlink_view)
        # Then
        self.assertTrue(actual.strict)
        self.assertTrue(actual.registered_classes.get('MockClass'), MockClass)
        self.assertEqual(downlink_view._lane_uri, actual.downlink_model.lane_uri)
        self.assertEqual(_DownlinkManagerStatus.CLOSED, actual.status)
        self.assertEqual(downlink_view._client, actual.downlink_model.client)
        self.assertEqual(downlink_view._node_uri, actual.downlink_model.node_uri)
        self.assertIsInstance(actual.downlink_model, _ValueDownlinkModel)
        self.assertEqual(downlink_view._host_uri, actual.downlink_model.host_uri)
        self.assertEqual(actual, actual.downlink_model.downlink_manager)
        self.assertEqual(actual.connection, actual.downlink_model.connection)
        self.assertEqual(actual.downlink_model.downlink_manager, actual)
        client.stop()

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_add_view_single(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://99.99.99.99:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('Hello')
        downlink_view.set_lane_uri('World')
        actual = _DownlinkManager(connection)
        # When
        await actual._add_view(downlink_view)
        # Then
        self.assertEqual(1, actual._view_count)
        self.assertIsInstance(actual.downlink_model, _ValueDownlinkModel)
        self.assertEqual(downlink_view._client, actual.downlink_model.client)
        self.assertEqual(downlink_view._host_uri, actual.downlink_model.host_uri)
        self.assertEqual(_DownlinkManagerStatus.OPEN, actual.status)
        self.assertEqual(downlink_view._node_uri, actual.downlink_model.node_uri)
        self.assertEqual(actual, actual.downlink_model.downlink_manager)
        self.assertEqual(downlink_view._lane_uri, actual.downlink_model.lane_uri)
        self.assertEqual(actual.connection, actual.downlink_model.connection)
        self.assertEqual(1, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertTrue(downlink_view._initialised.is_set())

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_add_view_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://11.22.33.44:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_node_uri('Goodbye')
        first_downlink_view.set_lane_uri('World')
        second_downlink_view = client.downlink_value()
        second_downlink_view.set_node_uri('Hello')
        second_downlink_view.set_lane_uri('World')
        third_downlink_view = client.downlink_value()
        third_downlink_view.set_node_uri('Dead')
        third_downlink_view.set_lane_uri('Parrot')
        actual = _DownlinkManager(connection)
        # When
        await actual._add_view(first_downlink_view)
        await actual._add_view(second_downlink_view)
        await actual._add_view(third_downlink_view)
        # Then
        self.assertEqual(_DownlinkManagerStatus.OPEN, actual.status)
        self.assertEqual(first_downlink_view._lane_uri, actual.downlink_model.lane_uri)
        self.assertEqual(first_downlink_view._node_uri, actual.downlink_model.node_uri)
        self.assertEqual(first_downlink_view._client, actual.downlink_model.client)
        self.assertEqual(3, actual._view_count)
        self.assertEqual(first_downlink_view._host_uri, actual.downlink_model.host_uri)
        self.assertIsInstance(actual.downlink_model, _ValueDownlinkModel)
        self.assertEqual(actual, actual.downlink_model.downlink_manager)
        self.assertEqual(actual.connection, actual.downlink_model.connection)
        self.assertEqual(1, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertTrue(first_downlink_view._initialised.is_set())
        self.assertTrue(second_downlink_view._initialised.is_set())
        self.assertTrue(third_downlink_view._initialised.is_set())

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_remove_view_single(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://11.11.11.11:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('Goodbye')
        downlink_view.set_lane_uri('World')
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        # When
        await actual._remove_view(downlink_view)
        # Then
        self.assertEqual(0, actual._view_count)
        self.assertEqual(downlink_view._client, actual.downlink_model.client)
        self.assertEqual(downlink_view._host_uri, actual.downlink_model.host_uri)
        self.assertEqual(_DownlinkManagerStatus.CLOSED, actual.status)
        self.assertIsInstance(actual.downlink_model, _ValueDownlinkModel)
        self.assertEqual(downlink_view._node_uri, actual.downlink_model.node_uri)
        self.assertEqual(actual, actual.downlink_model.downlink_manager)
        self.assertEqual(downlink_view._lane_uri, actual.downlink_model.lane_uri)
        self.assertEqual(actual.connection, actual.downlink_model.connection)
        self.assertEqual(2, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertTrue(downlink_view._initialised.is_set())

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_remove_view_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://44.33.22.11:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_node_uri('Dead')
        first_downlink_view.set_lane_uri('Parrot')
        second_downlink_view = client.downlink_value()
        second_downlink_view.set_node_uri('Hello')
        second_downlink_view.set_lane_uri('World')
        third_downlink_view = client.downlink_value()
        third_downlink_view.set_node_uri('Goodbye')
        third_downlink_view.set_lane_uri('World')
        actual = _DownlinkManager(connection)
        await actual._add_view(first_downlink_view)
        await actual._add_view(second_downlink_view)
        await actual._add_view(third_downlink_view)
        # When
        await actual._remove_view(second_downlink_view)
        await actual._remove_view(third_downlink_view)
        # Then
        self.assertEqual(1, actual._view_count)
        self.assertIsInstance(actual.downlink_model, _ValueDownlinkModel)
        self.assertEqual(_DownlinkManagerStatus.OPEN, actual.status)
        self.assertEqual(actual.connection, actual.downlink_model.connection)
        self.assertEqual(actual, actual.downlink_model.downlink_manager)
        self.assertEqual(1, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertTrue(first_downlink_view._initialised.is_set())
        self.assertTrue(second_downlink_view._initialised.is_set())
        self.assertTrue(third_downlink_view._initialised.is_set())

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_remove_view_non_existing(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://66.66.66.66:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('Foo')
        downlink_view.set_lane_uri('Qux')
        actual = _DownlinkManager(connection)
        # When
        await actual._remove_view(downlink_view)
        # Then
        self.assertEqual(0, actual._view_count)
        self.assertEqual(_DownlinkManagerStatus.CLOSED, actual.status)
        mock_schedule_task.assert_not_called()
        mock_send_message.assert_not_called()
        self.assertFalse(downlink_view._initialised.is_set())

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_receive_message_linked(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://66.66.66.66:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('test')
        downlink_view.set_lane_uri('foo')
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        envelope = _LinkedResponse('test', 'foo')
        # When
        await actual._receive_message(envelope)
        # Then
        self.assertTrue(actual.downlink_model.linked.is_set())
        self.assertEqual(1, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_receive_message_synced(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://11.11.11.11:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('test')
        downlink_view.set_lane_uri('foo')
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        envelope = _SyncedResponse('test', 'foo')
        # When
        await actual._receive_message(envelope)
        # Then
        self.assertTrue(actual.downlink_model._synced.is_set())
        self.assertEqual(1, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_receive_message_event(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://33.33.33.33:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('test')
        downlink_view.set_lane_uri('foo')
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        value = Text.create_from('baz')
        envelope = _EventMessage('test', 'foo', body=value)
        # When
        await actual._receive_message(envelope)
        # Then
        self.assertEqual(value.value, actual.downlink_model._value)
        self.assertEqual(1, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_receive_message_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://44.44.44.44:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('bar')
        downlink_view.set_lane_uri('baz')
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        linked_envelope = _LinkedResponse('bar', 'baz')
        value = Text.create_from('foo')
        event_envelope = _EventMessage('bar', 'baz', body=value)
        synced_envelope = _SyncedResponse('bar', 'baz')
        # When
        await actual._receive_message(linked_envelope)
        await actual._receive_message(event_envelope)
        await actual._receive_message(synced_envelope)
        # Then
        self.assertEqual(value.value, actual.downlink_model._value)
        self.assertTrue(actual.downlink_model._synced.is_set())
        self.assertTrue(actual.downlink_model.linked.is_set())
        self.assertEqual(1, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_did_set_single(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://4.3.2.1:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_value()
        downlink_view.set_node_uri('bar')
        downlink_view.set_lane_uri('baz')
        did_set_callback = mock_did_set_callback
        downlink_view.did_set(did_set_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        # When
        await actual._subscribers_did_set('dead', 'parrot')
        # Then
        self.assertEqual(2, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertEqual(did_set_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual('dead', mock_schedule_task.call_args_list[1][0][1])
        self.assertEqual('parrot', mock_schedule_task.call_args_list[1][0][2])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_did_set_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://10.9.8.7:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        did_set_callback = mock_did_set_callback
        first_downlink_view = client.downlink_value()
        first_downlink_view.set_node_uri('cow')
        first_downlink_view.set_lane_uri('moo')
        first_downlink_view.did_set(did_set_callback)
        second_downlink_view = client.downlink_value()
        second_downlink_view.set_node_uri('cow')
        second_downlink_view.set_lane_uri('moo')
        second_downlink_view.did_set(did_set_callback)
        third_downlink_view = client.downlink_value()
        third_downlink_view.set_node_uri('cow')
        third_downlink_view.set_lane_uri('moo')
        third_downlink_view.did_set(did_set_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(first_downlink_view)
        await actual._add_view(second_downlink_view)
        await actual._add_view(third_downlink_view)
        # When
        await actual._subscribers_did_set('hello', 'world')
        # Then
        self.assertEqual(6, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

        self.assertEqual(did_set_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual(Value.absent(), mock_schedule_task.call_args_list[1][0][1])
        self.assertEqual(Value.absent(), mock_schedule_task.call_args_list[1][0][2])

        self.assertEqual(did_set_callback, mock_schedule_task.call_args_list[2][0][0])
        self.assertEqual(Value.absent(), mock_schedule_task.call_args_list[2][0][1])
        self.assertEqual(Value.absent(), mock_schedule_task.call_args_list[2][0][2])

        self.assertEqual(did_set_callback, mock_schedule_task.call_args_list[3][0][0])
        self.assertEqual('hello', mock_schedule_task.call_args_list[3][0][1])
        self.assertEqual('world', mock_schedule_task.call_args_list[3][0][2])

        self.assertEqual(did_set_callback, mock_schedule_task.call_args_list[4][0][0])
        self.assertEqual('hello', mock_schedule_task.call_args_list[4][0][1])
        self.assertEqual('world', mock_schedule_task.call_args_list[4][0][2])

        self.assertEqual(did_set_callback, mock_schedule_task.call_args_list[5][0][0])
        self.assertEqual('hello', mock_schedule_task.call_args_list[5][0][1])
        self.assertEqual('world', mock_schedule_task.call_args_list[5][0][2])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_on_event_single(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://4.3.2.1:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_event()
        downlink_view.set_node_uri('bar')
        downlink_view.set_lane_uri('baz')
        on_event_callback = mock_on_event_callback
        downlink_view.on_event(on_event_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        # When
        await actual._subscribers_on_event('Hello, friend!')
        # Then
        self.assertEqual(2, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertEqual(on_event_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual('Hello, friend!', mock_schedule_task.call_args_list[1][0][1])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_on_event_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://10.9.8.7:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        on_event_callback = mock_on_event_callback
        first_downlink_view = client.downlink_event()
        first_downlink_view.set_node_uri('pow')
        first_downlink_view.set_lane_uri('poo')
        first_downlink_view.on_event(on_event_callback)
        second_downlink_view = client.downlink_event()
        second_downlink_view.set_node_uri('bow')
        second_downlink_view.set_lane_uri('boo')
        second_downlink_view.on_event(on_event_callback)
        third_downlink_view = client.downlink_event()
        third_downlink_view.set_node_uri('wow')
        third_downlink_view.set_lane_uri('woo')
        third_downlink_view.on_event(on_event_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(first_downlink_view)
        await actual._add_view(second_downlink_view)
        await actual._add_view(third_downlink_view)
        # When
        await actual._subscribers_on_event('Welcome home!')
        # Then
        self.assertEqual(4, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

        self.assertEqual(on_event_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual('Welcome home!', mock_schedule_task.call_args_list[1][0][1])

        self.assertEqual(on_event_callback, mock_schedule_task.call_args_list[2][0][0])
        self.assertEqual('Welcome home!', mock_schedule_task.call_args_list[2][0][1])

        self.assertEqual(on_event_callback, mock_schedule_task.call_args_list[3][0][0])
        self.assertEqual('Welcome home!', mock_schedule_task.call_args_list[3][0][1])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_did_update_single(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://4.3.2.1:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_map()
        downlink_view.set_node_uri('bar')
        downlink_view.set_lane_uri('baz')
        did_update_callback = mock_did_update_callback
        downlink_view.did_update(did_update_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        # When
        await actual._subscribers_did_update('Key', 'New_value', 'Old_Value')
        # Then
        self.assertEqual(2, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertEqual(did_update_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual('Key', mock_schedule_task.call_args_list[1][0][1])
        self.assertEqual('New_value', mock_schedule_task.call_args_list[1][0][2])
        self.assertEqual('Old_Value', mock_schedule_task.call_args_list[1][0][3])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_did_update_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://10.9.8.7:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        did_update_callback = mock_did_update_callback
        first_downlink_view = client.downlink_map()
        first_downlink_view.set_node_uri('pow')
        first_downlink_view.set_lane_uri('poo')
        first_downlink_view.did_update(did_update_callback)
        second_downlink_view = client.downlink_map()
        second_downlink_view.set_node_uri('bow')
        second_downlink_view.set_lane_uri('boo')
        second_downlink_view.did_update(did_update_callback)
        third_downlink_view = client.downlink_map()
        third_downlink_view.set_node_uri('wow')
        third_downlink_view.set_lane_uri('woo')
        third_downlink_view.did_update(did_update_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(first_downlink_view)
        await actual._add_view(second_downlink_view)
        await actual._add_view(third_downlink_view)
        # When
        await actual._subscribers_did_update('KeY', 'NeW', 'OlD')
        # Then
        self.assertEqual(4, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

        self.assertEqual(mock_did_update_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual('KeY', mock_schedule_task.call_args_list[1][0][1])
        self.assertEqual('NeW', mock_schedule_task.call_args_list[1][0][2])
        self.assertEqual('OlD', mock_schedule_task.call_args_list[1][0][3])

        self.assertEqual(mock_did_update_callback, mock_schedule_task.call_args_list[2][0][0])
        self.assertEqual('KeY', mock_schedule_task.call_args_list[2][0][1])
        self.assertEqual('NeW', mock_schedule_task.call_args_list[2][0][2])
        self.assertEqual('OlD', mock_schedule_task.call_args_list[2][0][3])

        self.assertEqual(mock_did_update_callback, mock_schedule_task.call_args_list[3][0][0])
        self.assertEqual('KeY', mock_schedule_task.call_args_list[3][0][1])
        self.assertEqual('NeW', mock_schedule_task.call_args_list[3][0][2])
        self.assertEqual('OlD', mock_schedule_task.call_args_list[3][0][3])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_did_remove_single(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://4.3.2.1:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_map()
        downlink_view.set_node_uri('bar')
        downlink_view.set_lane_uri('baz')
        did_remove_callback = mock_did_remove_callback
        downlink_view.did_remove(did_remove_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        # When
        await actual._subscribers_did_remove('Key', 'Old_Value')
        # Then
        self.assertEqual(2, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)
        self.assertEqual(did_remove_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual('Key', mock_schedule_task.call_args_list[1][0][1])
        self.assertEqual('Old_Value', mock_schedule_task.call_args_list[1][0][2])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_subscribers_did_remove_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://10.9.8.7:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        did_remove_callback = mock_on_event_callback
        first_downlink_view = client.downlink_map()
        first_downlink_view.set_node_uri('fall')
        first_downlink_view.set_lane_uri('boom')
        first_downlink_view.did_remove(did_remove_callback)
        second_downlink_view = client.downlink_map()
        second_downlink_view.set_node_uri('fall')
        second_downlink_view.set_lane_uri('boom')
        second_downlink_view.did_remove(did_remove_callback)
        third_downlink_view = client.downlink_map()
        third_downlink_view.set_node_uri('fall')
        third_downlink_view.set_lane_uri('boom')
        third_downlink_view.did_remove(did_remove_callback)
        actual = _DownlinkManager(connection)
        await actual._add_view(first_downlink_view)
        await actual._add_view(second_downlink_view)
        await actual._add_view(third_downlink_view)
        # When
        await actual._subscribers_did_remove('Bar', 'Baz')
        # Then
        self.assertEqual(4, mock_schedule_task.call_count)
        self.assertEqual(1, mock_send_message.call_count)

        self.assertEqual(did_remove_callback, mock_schedule_task.call_args_list[1][0][0])
        self.assertEqual('Bar', mock_schedule_task.call_args_list[1][0][1])
        self.assertEqual('Baz', mock_schedule_task.call_args_list[1][0][2])

        self.assertEqual(did_remove_callback, mock_schedule_task.call_args_list[2][0][0])
        self.assertEqual('Bar', mock_schedule_task.call_args_list[2][0][1])
        self.assertEqual('Baz', mock_schedule_task.call_args_list[2][0][2])

        self.assertEqual(did_remove_callback, mock_schedule_task.call_args_list[3][0][0])
        self.assertEqual('Bar', mock_schedule_task.call_args_list[3][0][1])
        self.assertEqual('Baz', mock_schedule_task.call_args_list[3][0][2])

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_close_views_single(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://4.3.2.1:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        downlink_view = client.downlink_map()
        downlink_view._is_open = True
        actual = _DownlinkManager(connection)
        await actual._add_view(downlink_view)
        # When
        actual._close_views()
        # Then
        self.assertFalse(downlink_view._is_open)
        self.assertTrue(mock_schedule_task.called)
        self.assertTrue(mock_send_message.called)

    @patch('swimos.client._connections._WSConnection._send_message', new_callable=MockAsyncFunction)
    @patch('swimos.SwimClient._schedule_task')
    async def test_downlink_manager_close_views_multiple(self, mock_schedule_task, mock_send_message):
        # Given
        host_uri = 'ws://4.3.2.1:9001'
        scheme = 'ws'
        connection = _WSConnection(host_uri, scheme)
        client = SwimClient()
        client._has_started = True
        actual = _DownlinkManager(connection)
        first_downlink_view = client.downlink_map()
        first_downlink_view._is_open = True
        second_downlink_view = client.downlink_map()
        second_downlink_view._is_open = True
        third_downlink_view = client.downlink_map()
        third_downlink_view._is_open = True
        await actual._add_view(first_downlink_view)
        await actual._add_view(second_downlink_view)
        await actual._add_view(third_downlink_view)
        # When
        actual._close_views()
        # Then
        self.assertFalse(first_downlink_view._is_open)
        self.assertFalse(second_downlink_view._is_open)
        self.assertFalse(third_downlink_view._is_open)
        self.assertTrue(mock_schedule_task.called)
        self.assertTrue(mock_send_message.called)
