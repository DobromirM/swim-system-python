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

from concurrent.futures import Future
from unittest.mock import patch

from swimos import SwimClient
from swimos.client._connections import _DownlinkManager, _DownlinkManagerStatus
from swimos.client._downlinks._downlinks import _EventDownlinkModel, _DownlinkModel, _ValueDownlinkModel, \
    _EventDownlinkView, \
    _DownlinkView, _ValueDownlinkView, _MapDownlinkModel, _MapDownlinkView
from swimos.client._downlinks._utils import UpdateRequest, RemoveRequest
from swimos.structures import Text, Attr, RecordMap, Num, Bool, Slot, Value
from swimos.structures._structs import _Absent, _Record
from swimos.warp._warp import _LinkedResponse, _SyncedResponse, _EventMessage, _UnlinkedResponse
from test.utils import MockConnection, MockExecuteOnException, MockWebsocketConnect, MockWebsocket, \
    mock_did_set_confirmation, ReceiveLoop, MockPerson, MockPet, NewScope, MockNoDefaultConstructor, MockCar, \
    MockModel, MockDownlinkManager, mock_on_event_callback, MockEventCallback, \
    MockDidSetCallback, mock_did_set_callback, MockDidUpdateCallback, mock_did_update_callback, \
    mock_did_remove_callback, MockDidRemoveCallback


class TestDownlinks(aiounittest.AsyncTestCase):

    def setUp(self):
        MockWebsocket.clear()
        MockConnection.clear()

    async def test_create_event_downlink_model(self):
        # Given
        with SwimClient() as client:
            # When
            actual = _EventDownlinkModel(client)

        # Then
        self.assertIsInstance(actual, _EventDownlinkModel)
        self.assertIsInstance(actual, _DownlinkModel)
        self.assertEqual(client, actual.client)
        self.assertFalse(actual.linked.is_set())

    async def test_open_downlink_model(self):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkModel(client)
            downlink.connection = MockConnection.get_mock_connection()
            # When
            actual = downlink._open()

            # Then
            self.assertFalse(actual.task.done())

        self.assertTrue(actual.task.done())
        self.assertEqual(downlink, actual)
        self.assertIsInstance(actual.task, Future)

    @patch('swimos.client._connections._DownlinkManager._close_views')
    async def test_close_downlink_model_with_manager(self, mock_close_views):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkModel(client)
            downlink.connection = MockConnection.get_mock_connection()
            downlink = downlink._open()
            manager = _DownlinkManager(MockConnection.get_mock_connection())
            downlink.downlink_manager = manager

            # When
            actual = downlink._close()
            while not actual.task.done():
                pass

        # Then
        self.assertEqual(downlink, actual)
        self.assertIsInstance(actual.task, Future)
        self.assertTrue(actual.task.done())
        self.assertTrue(actual.task.cancelled())
        self.assertTrue(mock_close_views.called)

    @patch('swimos.client._connections._DownlinkManager._close_views')
    async def test_close_downlink_model_without_manager(self, mock_close_views):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkModel(client)
            downlink.connection = MockConnection.get_mock_connection()
            downlink = downlink._open()

            # When
            actual = downlink._close()
            while not actual.task.done():
                pass

        # Then
        self.assertEqual(downlink, actual)
        self.assertIsInstance(actual.task, Future)
        self.assertTrue(actual.task.done())
        self.assertTrue(actual.task.cancelled())
        self.assertFalse(mock_close_views.called)

    async def test_downlink_model_receive_message_linked(self):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkModel(client)
            downlink.connection = MockConnection.get_mock_connection()
            downlink.connection.owner = downlink
            linked_message = _LinkedResponse('linked_node', 'linked_lane')
            downlink.connection.messages_to_receive.append(linked_message)

            # When
            actual = downlink._open()
            while not actual.linked.is_set():
                pass

        # Then
        self.assertEqual(downlink, actual)
        self.assertTrue(actual.linked.is_set())

    async def test_downlink_model_receive_message_synced(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkModel(client)
            downlink.connection = MockConnection.get_mock_connection()
            downlink.connection.owner = downlink
            synced_message = _SyncedResponse('synced_node', 'synced_lane')
            downlink.connection.messages_to_receive.append(synced_message)

            # When
            actual = downlink._open()
            while not actual._synced.is_set():
                pass

        # Then
        self.assertEqual(downlink, actual)
        self.assertTrue(actual._synced.is_set())

    async def test_downlink_model_receive_message_event(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkModel(client)
            downlink.connection = MockConnection.get_mock_connection()
            downlink.connection.owner = downlink
            downlink_manager = _DownlinkManager(downlink.connection)
            downlink.downlink_manager = downlink_manager
            event_message = _EventMessage('event_node', 'event_lane',
                                          _Record.create_from(Text.create_from('event_body')))
            downlink.connection.messages_to_receive.append(event_message)

            # When
            actual = downlink._open()
            while not actual._value:
                pass

        # Then
        self.assertEqual(downlink, actual)
        self.assertEqual('event_body', actual._value)

    @patch('warnings.warn')
    async def test_downlink_model_receive_message_unlinked(self, mock_warn):
        # Given
        with SwimClient(execute_on_exception=MockExecuteOnException.get_mock_execute_on_exception()) as client:
            downlink = _EventDownlinkModel(client)
            downlink.connection = MockConnection.get_mock_connection()
            downlink.connection.owner = downlink

            body = RecordMap.create()
            body.add(Attr.create_attr('laneNotFound', 'foo'))

            unlinked_message = _UnlinkedResponse('unlinked_node', 'unlinked_lane', body=body)
            downlink.connection.messages_to_receive.append(unlinked_message)

            # When
            actual = downlink._open()
            while not MockExecuteOnException.get_mock_execute_on_exception().called:
                pass

        # Then
        self.assertEqual(downlink, actual)
        self.assertEqual('Lane "None" was not found on the remote agent!', mock_warn.call_args_list[0][0][0])

    async def test_create_event_downlink_view(self):
        # Given
        with SwimClient() as client:
            # When
            actual = _EventDownlinkView(client)

        # Then
        self.assertIsInstance(actual, _EventDownlinkView)
        self.assertIsInstance(actual, _DownlinkView)
        self.assertEqual(client, actual._client)
        self.assertFalse(actual._is_open)
        self.assertFalse(actual.strict)

    async def test_downlink_view_set_host_uri_ws(self):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            host_uri = 'ws://127.0.0.1'
            # When
            actual = downlink.set_host_uri(host_uri)

        # Then
        self.assertEqual(downlink, actual)
        self.assertEqual(host_uri, actual._host_uri)

    async def test_downlink_view_set_host_uri_warp(self):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            host_uri = 'warp://127.0.0.1'
            # When
            actual = downlink.set_host_uri(host_uri)

        # Then
        self.assertEqual(downlink, actual)
        self.assertEqual('ws://127.0.0.1', actual._host_uri)

    @patch('warnings.warn')
    async def test_downlink_view_set_host_uri_after_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            host_uri = 'ws://127.0.0.1'
            downlink._is_open = True
            # When
            downlink.set_host_uri(host_uri)
        # Then
        self.assertEqual('Cannot execute "set_host_uri" after the downlink has been opened!',
                         mock_warn.mock_calls[0][1][0])

    async def test_downlink_view_set_node_uri(self):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            node_uri = 'boo/bar'
            # When
            actual = downlink.set_node_uri(node_uri)

        # Then
        self.assertEqual(downlink, actual)
        self.assertEqual(node_uri, actual._node_uri)

    @patch('warnings.warn')
    async def test_downlink_view_set_node_uri_after_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            node_uri = 'foo'
            downlink._is_open = True
            # When
            downlink.set_node_uri(node_uri)
        # Then
        self.assertEqual('Cannot execute "set_node_uri" after the downlink has been opened!',
                         mock_warn.mock_calls[0][1][0])

    async def test_downlink_view_set_lane_uri(self):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            lane_uri = 'shop'
            # When
            actual = downlink.set_lane_uri(lane_uri)

        # Then
        self.assertEqual(downlink, actual)
        self.assertEqual(lane_uri, actual._lane_uri)

    @patch('warnings.warn')
    async def test_downlink_view_set_lane_uri_after_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            lane_uri = 'bar'
            downlink._is_open = True
            # When
            downlink.set_lane_uri(lane_uri)
        # Then
        self.assertEqual('Cannot execute "set_lane_uri" after the downlink has been opened!',
                         mock_warn.mock_calls[0][1][0])

    async def test_downlink_view_route(self):
        # Given
        with SwimClient() as client:
            downlink = _EventDownlinkView(client)
            node_uri = 'boo/bar'
            lane_uri = 'shop'
            downlink.set_node_uri(node_uri)
            downlink.set_lane_uri(lane_uri)
            # When
            actual = downlink.route

        # Then
        self.assertEqual(f'{node_uri}/{lane_uri}', actual)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_open(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            # When
            actual = downlink.open()

            while loop_class.call_count == 0:
                pass

            # Then
            self.assertTrue(actual._is_open)

        self.assertFalse(actual._is_open)
        self.assertTrue(mock_websocket_connect.called)
        self.assertIsInstance(actual._model, _DownlinkModel)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_close(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.open()
            while loop_class.call_count == 0:
                pass
            # When
            actual = downlink.close()

        # Then
        self.assertFalse(actual._is_open)
        self.assertTrue(mock_websocket_connect.called)
        self.assertIsInstance(actual._model, _DownlinkModel)

    async def test_downlink_view_get_registered_classes_from_self(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            # When
            mock_person_class = MockPerson
            downlink.register_class(mock_person_class)

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_get_registered_classes_from_manager(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)

            # When
            mock_person_class = MockPerson
            downlink.register_class(mock_person_class)
            downlink.open()
            while loop_class.call_count == 0:
                pass

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))

    async def test_downlink_view_get_strict_from_self(self):
        # Given
        with SwimClient() as client:
            # When
            downlink = _ValueDownlinkView(client)

        # Then
        self.assertFalse(downlink.strict)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_get_strict_from_manager(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)

            # When
            downlink.open()
            while loop_class.call_count == 0:
                pass

        # Then
        self.assertFalse(downlink.strict)
        self.assertTrue(mock_websocket_connect.called)

    async def test_downlink_view_set_strict_to_self(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            # When
            downlink.strict = True

        # Then
        self.assertTrue(downlink.strict)

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_set_strict_to_manager(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.open()
            while loop_class.call_count == 0:
                pass

            # When
            downlink.strict = True

        # Then
        self.assertTrue(downlink.strict)
        self.assertTrue(mock_websocket_connect.called)

    async def test_downlink_view_register_classes(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            # When
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            downlink.register_classes([mock_person_class, mock_pet_class])

        # Then
        self.assertEqual(2, len(downlink.registered_classes))
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))
        self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))

    async def test_downlink_view_register_class_self(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            # When
            mock_pet_class = MockPet
            downlink.register_class(mock_pet_class)

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))

    async def test_downlink_view_register_deregistered_class_self(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            # When
            mock_pet_class = MockPet
            downlink.register_class(mock_pet_class)
            self.assertEqual(1, len(downlink.registered_classes))
            downlink.deregister_class(mock_pet_class)
            self.assertEqual(0, len(downlink.registered_classes))
            downlink.register_class(mock_pet_class)

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))

    async def test_downlink_view_overwrite_register_class_self(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            # When
            mock_person_class = MockPerson
            mock_second_person_class = NewScope.MockPerson
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_second_person_class)

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertEqual(mock_second_person_class, downlink.registered_classes.get('MockPerson'))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_register_class_downlink_manager(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.open()
            while loop_class.call_count == 0:
                pass
            # When
            mock_person_class = MockPerson
            downlink.register_class(mock_person_class)

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_overwrite_register_class_downlink_manager(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.open()
            while loop_class.call_count == 0:
                pass
            # When
            mock_person_class = MockPerson
            downlink.register_class(mock_person_class)
            mock_second_person_class = NewScope.MockPerson
            downlink.register_class(mock_second_person_class)

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)
        self.assertEqual(mock_second_person_class, downlink.registered_classes.get('MockPerson'))

    @patch('warnings.warn')
    async def test_downlink_view_register_class_exception_no_default_constructor(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            # When
            mock_no_default_constructor = MockNoDefaultConstructor
            downlink.register_class(mock_no_default_constructor)

        # Then
        self.assertEqual(
            'Class "MockNoDefaultConstructor" must have a default constructor or default values for all arguments!',
            mock_warn.mock_calls[0][1][0])
        self.assertEqual(0, len(downlink.registered_classes))

    async def test_downlink_view_deregister_all_classes_self(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            downlink.register_class(mock_car_class)
            self.assertTrue(3, len(downlink.registered_classes))
            # When
            downlink.deregister_all_classes()

        # Then
        self.assertEqual(0, len(downlink.registered_classes))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_deregister_all_classes_manager(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.open()
            while loop_class.call_count == 0:
                pass
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            downlink.register_class(mock_car_class)
            self.assertTrue(3, len(downlink.registered_classes))
            # When
            downlink.deregister_all_classes()

        # Then
        self.assertEqual(0, len(downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)

    async def test_downlink_view_deregister_classes(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            downlink.register_class(mock_car_class)
            self.assertTrue(3, len(downlink.registered_classes))
            # When
            downlink.deregister_classes([mock_pet_class, mock_person_class])

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertEqual(mock_car_class, downlink.registered_classes.get('MockCar'))

    async def test_downlink_view_deregister_class_self(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            downlink.register_class(mock_car_class)
            self.assertTrue(3, len(downlink.registered_classes))
            self.assertEqual(mock_car_class, downlink.registered_classes.get('MockCar'))
            self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))
            self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))
            # When
            downlink.deregister_class(mock_car_class)

        # Then
        self.assertEqual(2, len(downlink.registered_classes))
        self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))

    async def test_downlink_view_deregister_class_self_missing(self):
        # Given
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            self.assertTrue(2, len(downlink.registered_classes))
            self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))
            self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))
            # When
            downlink.deregister_class(mock_car_class)

        # Then
        self.assertEqual(2, len(downlink.registered_classes))
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))
        self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_deregister_class_manager(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.open()
            while loop_class.call_count == 0:
                pass
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            downlink.register_class(mock_car_class)
            self.assertTrue(3, len(downlink.registered_classes))
            # When
            downlink.deregister_class(mock_car_class)

        # Then
        self.assertEqual(2, len(downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))
        self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_deregister_class_manager_missing(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.open()
            while loop_class.call_count == 0:
                pass
            mock_person_class = MockPerson
            mock_pet_class = MockPet
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            self.assertTrue(2, len(downlink.registered_classes))
            # When
            downlink.deregister_class(mock_car_class)

        # Then
        self.assertEqual(2, len(downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))
        self.assertEqual(mock_pet_class, downlink.registered_classes.get('MockPet'))

    async def test_downlink_view_assign_manager(self):
        # Given
        connection = MockWebsocketConnect()
        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.strict = True
            mock_person_class = MockPerson
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_car_class)
            manager = _DownlinkManager(connection)
            manager.downlink_model = MockModel()
            # When
            await downlink._assign_manager(manager)

        # Then
        self.assertEqual(manager.downlink_model, downlink._model)
        self.assertEqual(manager.registered_classes, downlink.registered_classes)
        self.assertEqual(manager.strict, downlink.strict)
        self.assertEqual(manager, downlink._downlink_manager)
        self.assertTrue(manager.strict)
        self.assertIsInstance(manager.downlink_model, MockModel)
        self.assertEqual(2, len(manager.registered_classes))
        self.assertEqual(mock_person_class, manager.registered_classes.get('MockPerson'))
        self.assertEqual(mock_car_class, manager.registered_classes.get('MockCar'))

    async def test_downlink_view_initialise_model(self):
        # Given
        connection = MockWebsocketConnect()
        manager = _DownlinkManager(connection)
        with SwimClient() as client:
            model = _ValueDownlinkModel(client)
            downlink = _ValueDownlinkView(client)
            downlink.strict = True
            mock_person_class = MockPerson
            mock_car_class = MockCar
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_car_class)
            host_uri = 'ws://host_uri'
            lane_uri = 'lane/uri'
            node_uri = 'node_uri'
            downlink.set_host_uri(host_uri)
            downlink.set_lane_uri(lane_uri)
            downlink.set_node_uri(node_uri)
            # When
            await downlink._initalise_model(manager, model)

        # Then
        self.assertEqual(downlink.registered_classes, manager.registered_classes)
        self.assertEqual(downlink.strict, manager.strict)
        self.assertEqual(manager, model.downlink_manager)
        self.assertEqual(host_uri, model.host_uri)
        self.assertEqual(node_uri, model.node_uri)
        self.assertEqual(lane_uri, model.lane_uri)
        self.assertTrue(manager.strict)
        self.assertEqual(mock_person_class, manager.registered_classes.get('MockPerson'))
        self.assertEqual(mock_car_class, manager.registered_classes.get('MockCar'))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_register_and_deregister_classes(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        mock_person_class = MockPerson
        mock_pet_class = MockPet
        mock_car_class = MockCar

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            downlink.register_class(mock_car_class)
            downlink.open()

            while loop_class.call_count == 0:
                pass
            self.assertTrue(3, len(downlink.registered_classes))
            # When
            second_downlink = _ValueDownlinkView(client)
            second_downlink.set_host_uri('ws://127.0.0.1')
            second_downlink.set_node_uri('boo/bar')
            second_downlink.set_lane_uri('shop')
            second_downlink.deregister_class(mock_pet_class)
            second_downlink.open()
            self.assertTrue(2, len(downlink.registered_classes))
            second_downlink.deregister_class(mock_car_class)

        # Then
        self.assertEqual(1, len(downlink.registered_classes))
        self.assertEqual(1, len(second_downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)
        self.assertEqual(mock_person_class, downlink.registered_classes.get('MockPerson'))
        self.assertEqual(mock_person_class, second_downlink.registered_classes.get('MockPerson'))

    @patch('websockets.connect', new_callable=MockWebsocketConnect)
    async def test_downlink_view_register_and_deregister_all(self, mock_websocket_connect):
        # Given
        message = '@event(node:"boo/bar",lane:shop)'
        MockWebsocket.get_mock_websocket().messages_to_send.append(message)
        loop_class = ReceiveLoop()
        MockWebsocket.get_mock_websocket().custom_recv_func = loop_class.recv_loop

        mock_person_class = MockPerson
        mock_pet_class = MockPet
        mock_car_class = MockCar

        with SwimClient() as client:
            downlink = _ValueDownlinkView(client)
            downlink.set_host_uri('ws://127.0.0.1')
            downlink.set_node_uri('boo/bar')
            downlink.set_lane_uri('shop')
            downlink.did_set(mock_did_set_confirmation)
            downlink.register_class(mock_person_class)
            downlink.register_class(mock_pet_class)
            downlink.register_class(mock_car_class)
            downlink.open()

            while loop_class.call_count == 0:
                pass
            self.assertTrue(3, len(downlink.registered_classes))
            # When
            second_downlink = _ValueDownlinkView(client)
            second_downlink.set_host_uri('ws://127.0.0.1')
            second_downlink.set_node_uri('boo/bar')
            second_downlink.set_lane_uri('shop')
            second_downlink.deregister_all_classes()
            second_downlink.open()

        # Then
        self.assertEqual(0, len(downlink.registered_classes))
        self.assertEqual(0, len(second_downlink.registered_classes))
        self.assertTrue(mock_websocket_connect.called)

    async def test_event_downlink_model_establish_downlink(self):
        # Given
        with SwimClient() as client:
            downlink_model = _EventDownlinkModel(client)
            downlink_model.node_uri = 'foo'
            downlink_model.lane_uri = 'bar'
            downlink_model.connection = MockConnection()

            # When
            await downlink_model._establish_downlink()

        # Then
        self.assertEqual(1, len(downlink_model.connection.messages_sent))
        self.assertEqual('@link(node:foo,lane:bar)', downlink_model.connection.messages_sent[0])

    async def test_event_downlink_model_received_synced(self):
        # Given
        client = SwimClient()
        downlink_model = _EventDownlinkModel(client)
        # When
        with self.assertRaises(TypeError) as error:
            await downlink_model._receive_synced()

        # Then
        message = error.exception.args[0]
        self.assertEqual(message, 'Event downlink does not support synced responses!')

    async def test_event_downlink_receive_event_absent(self):
        # Given
        client = SwimClient()
        downlink_model = _EventDownlinkModel(client)
        # noinspection PyTypeChecker
        mock_manager = MockDownlinkManager()
        downlink_model.downlink_manager = mock_manager
        event_message = _EventMessage(node_uri='foo', lane_uri='bar')
        # When
        await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertIsInstance(mock_manager.event, _Absent)

    async def test_event_downlink_receive_event_text(self):
        # Given
        client = SwimClient()
        downlink_model = _EventDownlinkModel(client)
        # noinspection PyTypeChecker
        mock_manager = MockDownlinkManager()
        downlink_model.downlink_manager = mock_manager
        event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=Text.create_from('message'))
        # When
        await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual('message', mock_manager.event)

    async def test_event_downlink_receive_event_num(self):
        # Given
        client = SwimClient()
        downlink_model = _EventDownlinkModel(client)
        # noinspection PyTypeChecker
        mock_manager = MockDownlinkManager()
        downlink_model.downlink_manager = mock_manager
        event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=Num.create_from(21))
        # When
        await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(21, mock_manager.event)

    async def test_event_downlink_receive_event_bool(self):
        # Given
        client = SwimClient()
        downlink_model = _EventDownlinkModel(client)
        # noinspection PyTypeChecker
        mock_manager = MockDownlinkManager()
        downlink_model.downlink_manager = mock_manager
        event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=Bool.create_from(True))
        # When
        await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(True, mock_manager.event)

    async def test_event_downlink_receive_event_object(self):
        # Given
        client = SwimClient()
        downlink_model = _EventDownlinkModel(client)
        # noinspection PyTypeChecker
        mock_manager = MockDownlinkManager()
        downlink_model.downlink_manager = mock_manager
        recon_person = RecordMap.create()
        recon_person.add(Attr.create_attr('MockPerson', Value.extant()))
        recon_person.add(Slot.create_slot(Text.create_from('name'), Text.create_from('George')))
        recon_person.add(Slot.create_slot(Text.create_from('age'), Num.create_from(25)))
        event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=recon_person)
        # When
        await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(25, mock_manager.event.age)
        self.assertEqual('George', mock_manager.event.name)

    async def test_event_downlink_view_register_manager(self):
        # Given
        client = SwimClient()
        downlink_view = _EventDownlinkView(client)
        downlink_model = _EventDownlinkModel(client)
        connection = MockConnection()
        # noinspection PyTypeChecker
        manager = _DownlinkManager(connection)
        manager.downlink_model = downlink_model
        # When
        await downlink_view._register_manager(manager)
        # Then
        self.assertEqual(downlink_model, downlink_view._model)
        self.assertEqual(manager, downlink_view._downlink_manager)

    async def test_event_downlink_view_create_downlink_model(self):
        # Given
        client = SwimClient()
        connection = MockConnection()
        # noinspection PyTypeChecker
        manager = _DownlinkManager(connection)
        host_uri = 'ws://foo.bar'
        node_uri = 'baz'
        lane_uri = 'qux'
        downlink_view = _EventDownlinkView(client)
        downlink_view.set_host_uri(host_uri)
        downlink_view.set_node_uri(node_uri)
        downlink_view.set_lane_uri(lane_uri)
        downlink_view.strict = True
        mock_person_class = MockPerson
        downlink_view.register_class(mock_person_class)
        # When
        actual = await downlink_view._create_downlink_model(manager)
        # Then
        self.assertIsInstance(actual, _EventDownlinkModel)
        self.assertEqual(client, actual.client)
        self.assertEqual(downlink_view.strict, actual.downlink_manager.strict)
        self.assertEqual(downlink_view.registered_classes, actual.downlink_manager.registered_classes)
        self.assertEqual(downlink_view._host_uri, actual.host_uri)
        self.assertEqual(downlink_view._node_uri, actual.node_uri)
        self.assertEqual(downlink_view._lane_uri, actual.lane_uri)

    async def test_event_downlink_view_execute_on_event(self):
        # Given
        with SwimClient() as client:
            downlink_view = _EventDownlinkView(client)
            mock_on_event = MockEventCallback()
            downlink_view._on_event_callback = mock_on_event.execute
            event = 20
            # When
            await downlink_view._execute_on_event(event)
            while not mock_on_event.called:
                pass

        # Then
        self.assertEqual(20, mock_on_event.event)
        self.assertTrue(mock_on_event.called)

    async def test_event_downlink_view_execute_on_event_missing_callback(self):
        # Given
        with SwimClient() as client:
            downlink_view = _EventDownlinkView(client)
            event = 20
            # When
            with patch('swimos.SwimClient._schedule_task') as mock_schedule_task:
                await downlink_view._execute_on_event(event)

        # Then
        self.assertFalse(mock_schedule_task.called)

    async def test_event_downlink_view_set_on_event(self):
        # Given
        client = SwimClient()
        downlink_view = _EventDownlinkView(client)
        # When
        downlink_view.on_event(mock_on_event_callback)
        # Then
        self.assertEqual(mock_on_event_callback, downlink_view._on_event_callback)

    async def test_event_downlink_view_set_on_event_invalid(self):
        # Given
        client = SwimClient()
        downlink_view = _EventDownlinkView(client)
        # When
        with self.assertRaises(TypeError) as error:
            # noinspection PyTypeChecker
            downlink_view.on_event(222)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Callback must be a coroutine or a function!', message)

    async def test_create_value_downlink_model(self):
        # Given
        with SwimClient() as client:
            # When
            actual = _ValueDownlinkModel(client)

        # Then
        self.assertIsInstance(actual, _ValueDownlinkModel)
        self.assertIsInstance(actual, _DownlinkModel)
        self.assertEqual(client, actual.client)
        self.assertFalse(actual.linked.is_set())
        self.assertFalse(actual._synced.is_set())
        self.assertFalse(actual._value)
        self.assertEqual(actual._value, Value.absent())

    async def test_value_downlink_model_establish_downlink(self):

        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            downlink_model.node_uri = 'foo'
            downlink_model.lane_uri = 'bar'
            downlink_model.connection = MockConnection()

            # When
            await downlink_model._establish_downlink()

        # Then
        self.assertEqual(1, len(downlink_model.connection.messages_sent))
        self.assertEqual('@sync(node:foo,lane:bar)', downlink_model.connection.messages_sent[0])

    async def test_value_downlink_model_receive_synced(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            # When
            await downlink_model._receive_synced()
        # Then
        self.assertTrue(downlink_model._synced.is_set())

    async def test_value_downlink_model_receive_event_absent(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            # When
            event_message = _EventMessage(node_uri='foo', lane_uri='bar')
            await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(Value.absent(), downlink_model._value)
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(Value.absent(), mock_manager.did_set_new)
        self.assertEqual(Value.absent(), mock_manager.did_set_old)

    async def test_value_downlink_model_receive_event_text(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            # When
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=Text.create_from('value_text'))
            await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual('value_text', downlink_model._value)
        self.assertEqual(1, mock_manager.called)
        self.assertEqual('value_text', mock_manager.did_set_new)
        self.assertEqual(Value.absent(), mock_manager.did_set_old)

    async def test_value_downlink_model_receive_event_num(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            # When
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=Num.create_from(11))
            await downlink_model._receive_event(event_message)
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=Num.create_from(50))
            await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(50, downlink_model._value)
        self.assertEqual(2, mock_manager.called)
        self.assertEqual(50, mock_manager.did_set_new)
        self.assertEqual(11, mock_manager.did_set_old)

    async def test_value_downlink_model_receive_event_bool(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            # When
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=Bool.create_from(True))
            await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual(True, downlink_model._value)
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(True, mock_manager.did_set_new)
        self.assertEqual(Value.absent(), mock_manager.did_set_old)

    async def test_value_downlink_model_receive_event_object(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            recon_person = RecordMap.create()
            recon_person.add(Attr.create_attr('MockPerson', Value.extant()))
            recon_person.add(Slot.create_slot(Text.create_from('name'), Text.create_from('Peter')))
            recon_person.add(Slot.create_slot(Text.create_from('age'), Num.create_from(90)))
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=recon_person)
            # When
            await downlink_model._receive_event(event_message)
        # Then
        self.assertEqual('Peter', downlink_model._value.name)
        self.assertEqual(90, downlink_model._value.age)
        self.assertEqual(1, mock_manager.called)
        self.assertEqual('Peter', mock_manager.did_set_new.name)
        self.assertEqual(90, mock_manager.did_set_new.age)
        self.assertEqual(Value.absent(), mock_manager.did_set_old)

    async def test_value_downlink_model_send_message(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            downlink_model.connection = MockConnection.get_mock_connection()
            downlink_model.connection.owner = downlink_model
            downlink_model.linked.set()
            recon_person = RecordMap.create()
            recon_person.add(Attr.create_attr('MockPerson', Value.extant()))
            recon_person.add(Slot.create_slot(Text.create_from('name'), Text.create_from('Peter')))
            recon_person.add(Slot.create_slot(Text.create_from('age'), Num.create_from(90)))
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=recon_person)
            # When
            await downlink_model._send_message(event_message)
        # Then
        self.assertEqual('@event(node:foo,lane:bar)@MockPerson{name:Peter,age:90}',
                         MockConnection.get_mock_connection().messages_sent[0])

    async def test_value_downlink_model_get_value(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            downlink_model.connection = MockConnection.get_mock_connection()
            downlink_model.connection.owner = downlink_model
            downlink_model._value = 'Test_Value'
            downlink_model._synced.set()
            # When
            actual = await downlink_model._get_value()
        # Then
        self.assertEqual('Test_Value', actual)

    async def test_create_value_downlink_view(self):
        # Given
        with SwimClient() as client:
            # When
            actual = _ValueDownlinkView(client)

        # Then
        self.assertIsInstance(actual, _ValueDownlinkView)
        self.assertIsInstance(actual, _DownlinkView)
        self.assertEqual(client, actual._client)
        self.assertFalse(actual._is_open)
        self.assertFalse(actual.strict)
        self.assertIsNone(actual._did_set_callback)
        self.assertFalse(actual._initialised.is_set())

    async def test_value_downlink_view_register_manager_first_time(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            downlink_model = _ValueDownlinkModel(client)
            connection = MockConnection()
            # noinspection PyTypeChecker
            manager = _DownlinkManager(connection)
            manager.downlink_model = downlink_model
            # When
            await downlink_view._register_manager(manager)

        # Then
        self.assertTrue(downlink_view._initialised.is_set())
        self.assertEqual(downlink_model, downlink_view._model)
        self.assertEqual(manager, downlink_view._downlink_manager)

    async def test_value_downlink_view_register_manager_already_existing(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            mock_did_set = MockDidSetCallback()
            downlink_view.did_set(mock_did_set.execute)
            downlink_model = _ValueDownlinkModel(client)
            downlink_model._value = 'Foo'
            connection = MockConnection()
            # noinspection PyTypeChecker
            manager = _DownlinkManager(connection)
            manager.downlink_model = downlink_model
            manager.status = _DownlinkManagerStatus.OPEN
            # When
            await downlink_view._register_manager(manager)

            while not mock_did_set.called:
                pass

        # Then
        self.assertTrue(downlink_view._initialised.is_set())
        self.assertEqual(downlink_model, downlink_view._model)
        self.assertEqual(manager, downlink_view._downlink_manager)
        self.assertTrue(mock_did_set.called)
        self.assertEqual('Foo', mock_did_set.new_value)
        self.assertEqual(Value.absent(), mock_did_set.old_value)

    async def test_value_downlink_view_create_downlink_model(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            connection = MockConnection()
            host_uri = 'ws://value.downlink'
            node_uri = 'value'
            lane_uri = 'downlink'
            downlink_view.set_host_uri(host_uri)
            downlink_view.set_node_uri(node_uri)
            downlink_view.set_lane_uri(lane_uri)
            # noinspection PyTypeChecker
            manager = _DownlinkManager(connection)
            # When
            actual = await downlink_view._create_downlink_model(manager)

        # Then
        self.assertIsInstance(actual, _ValueDownlinkModel)
        self.assertEqual(client, actual.client)
        self.assertEqual(host_uri, actual.host_uri)
        self.assertEqual(node_uri, actual.node_uri)
        self.assertEqual(lane_uri, actual.lane_uri)
        self.assertEqual(manager, actual.downlink_manager)

    async def test_value_downlink_view_did_set_valid(self):
        # Given
        client = SwimClient()
        downlink_view = _ValueDownlinkView(client)
        function = mock_did_set_callback
        # When
        downlink_view.did_set(function)
        # Then
        self.assertTrue(function, downlink_view._did_set_callback)

    async def test_value_downlink_view_did_set_invalid(self):
        # Given
        client = SwimClient()
        downlink_view = _ValueDownlinkView(client)
        function = 111
        # When
        with self.assertRaises(TypeError) as error:
            # noinspection PyTypeChecker
            downlink_view.did_set(function)

        # Then
        message = error.exception.args[0]
        self.assertEqual(message, 'Callback must be a coroutine or a function!')

    async def test_value_downlink_view_value_no_model(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            # When
            actual = downlink_view._value

        # Then
        self.assertEqual(Value.absent(), actual)

    async def test_value_downlink_view_value_with_model(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            downlink_view._model = _ValueDownlinkModel(client)
            downlink_view._model._value = 50
            # When
            actual = downlink_view._value

        # Then
        self.assertEqual(50, actual)

    async def test_value_downlink_view_get_immediate(self):
        # Given
        client = SwimClient()
        downlink_view = _ValueDownlinkView(client)
        downlink_model = _ValueDownlinkModel(client)
        downlink_model._value = 41
        downlink_view._model = downlink_model
        downlink_view._is_open = True
        # When
        actual = downlink_view.get(False)
        # Then
        self.assertEqual(41, actual)

    async def test_value_downlink_view_get_with_wait(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            downlink_model = _ValueDownlinkModel(client)
            downlink_model._value = 'Some text'
            downlink_model._synced.set()
            downlink_view._model = downlink_model
            downlink_view._initialised.set()
            downlink_view._is_open = True
            # When
            actual = downlink_view.get(wait_sync=True)

        # Then
        self.assertEqual('Some text', actual)

    @patch('warnings.warn')
    async def test_value_downlink_view_get_before_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            # When
            downlink_view.get()

        # Then
        self.assertEqual('Cannot execute "get" before the downlink has been opened!', mock_warn.call_args_list[0][0][0])

    @patch('concurrent.futures._base.Future.result')
    async def test_value_downlink_view_set_blocking(self, mock_result):
        # Given
        with SwimClient() as client:
            node_uri = 'bar_node'
            lane_uri = 'foo_lane'

            downlink_model = _ValueDownlinkModel(client)
            downlink_model.linked.set()
            mock_connection = MockConnection()
            downlink_model.connection = mock_connection
            downlink_model.node_uri = node_uri
            downlink_model.lane_uri = lane_uri

            downlink_view = _ValueDownlinkView(client)
            downlink_view._initialised.set()
            downlink_view._model = downlink_model
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            downlink_view._is_open = True
            # When
            downlink_view.set(66, blocking=True)
        # Then
        self.assertEqual('@command(node:bar_node,lane:foo_lane)66', mock_connection.messages_sent[0])
        self.assertTrue(mock_result.called)

    @patch('concurrent.futures._base.Future.result')
    async def test_value_downlink_view_set_non_blocking(self, mock_result):
        # Given
        with SwimClient() as client:
            node_uri = 'bar_node'
            lane_uri = 'foo_lane'

            downlink_model = _ValueDownlinkModel(client)
            downlink_model.linked.set()
            mock_connection = MockConnection()
            downlink_model.connection = mock_connection
            downlink_model.node_uri = node_uri
            downlink_model.lane_uri = lane_uri

            downlink_view = _ValueDownlinkView(client)
            downlink_view._initialised.set()
            downlink_view._model = downlink_model
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            downlink_view._is_open = True
            # When
            downlink_view.set(66, blocking=False)
        # Then
        self.assertEqual('@command(node:bar_node,lane:foo_lane)66', mock_connection.messages_sent[0])
        self.assertFalse(mock_result.called)

    @patch('warnings.warn')
    async def test_value_downlink_view_set_before_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            # When
            downlink_view.set('value')

        # Then
        self.assertEqual('Cannot execute "set" before the downlink has been opened!', mock_warn.call_args_list[0][0][0])

    async def test_value_downlink_view_execute_did_set(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            mock_did_set = MockDidSetCallback()
            downlink_view._did_set_callback = mock_did_set.execute
            new_value = 'Test_new_value'
            old_value = 'Test_old_value'
            # When
            await downlink_view._execute_did_set(new_value, old_value)
            while not mock_did_set.called:
                pass
        # Then
        self.assertEqual(new_value, mock_did_set.new_value)
        self.assertEqual(old_value, mock_did_set.old_value)

    async def test_value_downlink_view_execute_did_set_no_callback(self):
        # Given
        with SwimClient() as client:
            downlink_view = _ValueDownlinkView(client)
            new_value = 'Test_new_value'
            old_value = 'Test_old_value'
            # When
            with patch('swimos.SwimClient._schedule_task') as mock_schedule_task:
                await downlink_view._execute_did_set(new_value, old_value)

        # Then
        self.assertFalse(mock_schedule_task.called)

    async def test_value_downlink_view_send_message(self):
        # Given
        with SwimClient() as client:
            downlink_model = _ValueDownlinkModel(client)
            downlink_model.linked.set()
            mock_connection = MockConnection()
            downlink_model.connection = mock_connection

            downlink_view = _ValueDownlinkView(client)
            downlink_view._initialised.set()
            downlink_view._model = downlink_model
            downlink_view._node_uri = 'node_bar'
            downlink_view._lane_uri = 'lane_baz'
            # When
            await downlink_view._send_message(2020)
        # Then
        self.assertEqual('@command(node:node_bar,lane:lane_baz)2020', mock_connection.messages_sent[0])

    async def test_create_map_downlink_model(self):
        # Given
        with SwimClient() as client:
            # When
            actual = _MapDownlinkModel(client)

        # Then
        self.assertIsInstance(actual, _MapDownlinkModel)
        self.assertIsInstance(actual, _DownlinkModel)
        self.assertEqual(client, actual.client)
        self.assertFalse(actual.linked.is_set())
        self.assertIsInstance(actual._map, dict)
        self.assertFalse(actual._synced.is_set())

    async def test_map_downlink_model_establish_downlink(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            downlink_model.node_uri = 'dog'
            downlink_model.lane_uri = 'bark'
            downlink_model.connection = MockConnection()

            # When
            await downlink_model._establish_downlink()

        # Then
        self.assertEqual(1, len(downlink_model.connection.messages_sent))
        self.assertEqual('@sync(node:dog,lane:bark)', downlink_model.connection.messages_sent[0])

    async def test_map_downlink_model_receive_synced(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # When
            await downlink_model._receive_synced()
        # Then
        self.assertTrue(downlink_model._synced.is_set())

    async def test_map_downlink_model_receive_event_update_primitive(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            downlink_model._synced.set()
            update_request = UpdateRequest('Elliot', 29)
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=update_request.to_record())
            # When
            await downlink_model._receive_event(event_message)

        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual('Elliot', mock_manager.update_key)
        self.assertEqual(29, mock_manager.update_value_new)
        self.assertEqual(Value.absent(), mock_manager.update_value_old)

    async def test_map_downlink_model_receive_event_update_object(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            mock_manager.registered_classes['MockPerson'] = MockPerson
            downlink_model.downlink_manager = mock_manager
            downlink_model._synced.set()
            person = MockPerson(name='Elliot', age=29)
            update_request = UpdateRequest(person, 'Hello')
            event_message = _EventMessage(node_uri='baz', lane_uri='qux', body=update_request.to_record())
            # When
            await downlink_model._receive_event(event_message)

        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(person.name, mock_manager.update_key.name)
        self.assertEqual(person.age, mock_manager.update_key.age)
        self.assertEqual('Hello', mock_manager.update_value_new)
        self.assertEqual(Value.absent(), mock_manager.update_value_old)

    async def test_map_downlink_model_receive_event_update_primitive_existing(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            downlink_model._synced.set()
            downlink_model._map['Elliot'] = ('Elliot', 11)
            update_request = UpdateRequest('Elliot', 29)
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=update_request.to_record())
            # When
            await downlink_model._receive_event(event_message)

        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual('Elliot', mock_manager.update_key)
        self.assertEqual(29, mock_manager.update_value_new)
        self.assertEqual(11, mock_manager.update_value_old)

    async def test_map_downlink_model_receive_event_update_object_existing(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            mock_manager.registered_classes['MockPerson'] = MockPerson
            downlink_model.downlink_manager = mock_manager
            downlink_model._synced.set()
            person = MockPerson(name='Elliot', age=29)
            downlink_model._map['@MockPerson{name:Elliot,age:29}'] = (person, 'bar')
            update_request = UpdateRequest(person, 'Hello')
            event_message = _EventMessage(node_uri='baz', lane_uri='qux', body=update_request.to_record())
            # When
            await downlink_model._receive_event(event_message)

        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(person.name, mock_manager.update_key.name)
        self.assertEqual(person.age, mock_manager.update_key.age)
        self.assertEqual('Hello', mock_manager.update_value_new)
        self.assertEqual('bar', mock_manager.update_value_old)

    async def test_map_downlink_model_receive_event_remove_primitive(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            downlink_model._synced.set()
            downlink_model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            remove_request = RemoveRequest('b')
            event_message = _EventMessage(node_uri='baz', lane_uri='qux', body=remove_request.to_record())
            # When
            await downlink_model._receive_event(event_message)

        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual('b', mock_manager.remove_key)
        self.assertEqual(2, mock_manager.remove_old_value)

    async def test_map_downlink_model_receive_event_remove_object(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            downlink_model._synced.set()

            first_person = MockPerson(name='Foo', age=1)
            second_person = MockPerson(name='Bar', age=2)

            downlink_model._map = {'@MockPerson{name:Foo,age:1}': (first_person, 'a'),
                                   '@MockPerson{name:Bar,age:2}': (second_person, 'b')}

            remove_request = RemoveRequest(first_person)
            event_message = _EventMessage(node_uri='baz', lane_uri='qux', body=remove_request.to_record())
            # When
            await downlink_model._receive_event(event_message)

        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual(first_person.name, mock_manager.remove_key.name)
        self.assertEqual(first_person.age, mock_manager.remove_key.age)
        self.assertEqual('a', mock_manager.remove_old_value)

    async def test_map_downlink_model_receive_event_remove_missing(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            # noinspection PyTypeChecker
            mock_manager = MockDownlinkManager()
            downlink_model.downlink_manager = mock_manager
            downlink_model._synced.set()
            remove_request = RemoveRequest('b')
            event_message = _EventMessage(node_uri='baz', lane_uri='qux', body=remove_request.to_record())
            # When
            await downlink_model._receive_event(event_message)

        # Then
        self.assertEqual(1, mock_manager.called)
        self.assertEqual('b', mock_manager.remove_key)
        self.assertEqual(Value.absent(), mock_manager.remove_old_value)

    async def test_map_downlink_model_send_message(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            downlink_model.connection = MockConnection.get_mock_connection()
            downlink_model.connection.owner = downlink_model
            downlink_model.linked.set()
            update_request = UpdateRequest('Elliot', 29)
            event_message = _EventMessage(node_uri='foo', lane_uri='bar', body=update_request.to_record())
            # When
            await downlink_model._send_message(event_message)

        # Then
        self.assertEqual('@event(node:foo,lane:bar)@update(key:Elliot)29',
                         MockConnection.get_mock_connection().messages_sent[0])

    async def test_map_downlink_model_get_value_with_key(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            downlink_model._synced.set()
            downlink_model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            # When
            actual = await downlink_model._get_value('b')

        # Then
        self.assertEqual(2, actual)

    async def test_map_downlink_model_get_value_with_key_missing(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            downlink_model._synced.set()
            downlink_model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            # When
            actual = await downlink_model._get_value('f')

        # Then
        self.assertEqual(Value.absent(), actual)

    async def test_map_downlink_model_get_values_primitive(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            downlink_model._synced.set()
            downlink_model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            # When
            actual = await downlink_model._get_values()

        # Then
        self.assertIsInstance(actual, list)
        self.assertEqual(5, len(actual))
        self.assertEqual('a', actual[0][0])
        self.assertEqual(1, actual[0][1])
        self.assertEqual('b', actual[1][0])
        self.assertEqual(2, actual[1][1])
        self.assertEqual('c', actual[2][0])
        self.assertEqual(3, actual[2][1])
        self.assertEqual('d', actual[3][0])
        self.assertEqual(4, actual[3][1])
        self.assertEqual('e', actual[4][0])
        self.assertEqual(5, actual[4][1])

    async def test_map_downlink_model_get_values_objects(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            downlink_model._synced.set()
            first_person = MockPerson(name='Foo', age=1)
            second_person = MockPerson(name='Bar', age=2)
            downlink_model._map = {'@MockPerson{name:Foo,age:1}': (first_person, 'a'),
                                   '@MockPerson{name:Bar,age:2}': (second_person, 'b')}
            # When
            actual = await downlink_model._get_values()

        # Then
        self.assertIsInstance(actual, list)
        self.assertEqual(2, len(actual))
        self.assertEqual(first_person, actual[0][0])
        self.assertEqual('a', actual[0][1])
        self.assertEqual(second_person, actual[1][0])
        self.assertEqual('b', actual[1][1])

    async def test_map_downlink_model_get_values_empty(self):
        # Given
        with SwimClient() as client:
            downlink_model = _MapDownlinkModel(client)
            downlink_model._synced.set()
            # When
            actual = await downlink_model._get_values()

        # Then
        self.assertIsInstance(actual, list)
        self.assertEqual(0, len(actual))

    async def test_map_downlink_view(self):
        # Given
        with SwimClient() as client:
            # When
            actual = _MapDownlinkView(client)

        # Then
        self.assertIsInstance(actual, _MapDownlinkView)
        self.assertIsInstance(actual, _DownlinkView)
        self.assertEqual(client, actual._client)
        self.assertFalse(actual._is_open)
        self.assertFalse(actual.strict)
        self.assertIsNone(actual._did_update_callback)
        self.assertIsNone(actual._did_remove_callback)
        self.assertFalse(actual._initialised.is_set())

    async def test_map_downlink_view_register_manager_first_time(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            connection = MockConnection()
            downlink_model = _ValueDownlinkModel(client)
            # noinspection PyTypeChecker
            manager = _DownlinkManager(connection)
            manager.downlink_model = downlink_model
            # When
            await downlink_view._register_manager(manager)
        # Then
        self.assertTrue(downlink_view._initialised.is_set())
        self.assertEqual(downlink_model, downlink_view._model)
        self.assertEqual(manager, downlink_view._downlink_manager)

    async def test_map_downlink_view_register_manager_already_existing(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            mock_did_update = MockDidUpdateCallback()
            downlink_view.did_update(mock_did_update.execute)
            downlink_model = _MapDownlinkModel(client)
            downlink_model._map = {'a': ('a', 1)}
            connection = MockConnection()
            # noinspection PyTypeChecker
            manager = _DownlinkManager(connection)
            manager.downlink_model = downlink_model
            manager.status = _DownlinkManagerStatus.OPEN
            # When
            await downlink_view._register_manager(manager)

            while not mock_did_update.called:
                pass

        # Then
        self.assertTrue(downlink_view._initialised.is_set())
        self.assertEqual(downlink_model, downlink_view._model)
        self.assertEqual(manager, downlink_view._downlink_manager)
        self.assertTrue(mock_did_update.called)
        self.assertEqual('a', mock_did_update.key)
        self.assertEqual(1, mock_did_update.new_value)
        self.assertEqual(Value.absent(), mock_did_update.old_value)

    async def test_map_downlink_view_create_downlink_model(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            host_uri = 'ws://127.0.0.1'
            node_uri = 'map_node'
            lane_uri = 'map_lane'
            downlink_view._host_uri = host_uri
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            connection = MockConnection()
            # noinspection PyTypeChecker
            manager = _DownlinkManager(connection)
            # When
            actual = await downlink_view._create_downlink_model(manager)

        # Then
        self.assertIsInstance(actual, _MapDownlinkModel)
        self.assertEqual(client, actual.client)
        self.assertEqual(host_uri, actual.host_uri)
        self.assertEqual(node_uri, actual.node_uri)
        self.assertEqual(lane_uri, actual.lane_uri)
        self.assertEqual(manager, actual.downlink_manager)

    async def test_map_downlink_view_map_no_model(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            key = 'foo'
            # When
            actual = downlink_view._map(key)

        # Then
        self.assertEqual(Value.absent(), actual)

    async def test_map_downlink_view_map_key_existing(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            model = _MapDownlinkModel(client)
            model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            key = 'c'
            downlink_view._model = model
            # When
            actual = downlink_view._map(key)

        # Then
        self.assertEqual(3, actual)

    async def test_map_downlink_view_map_key_missing(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            model = _MapDownlinkModel(client)
            model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            key = 'n'
            downlink_view._model = model
            # When
            actual = downlink_view._map(key)

        # Then
        self.assertEqual(Value.absent(), actual)

    async def test_map_downlink_view_map_all(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            model = _MapDownlinkModel(client)
            model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            downlink_view._model = model
            # When
            actual = downlink_view._map(None)

        # Then
        self.assertEqual(5, len(actual))
        self.assertEqual('a', actual[0][0])
        self.assertEqual(1, actual[0][1])
        self.assertEqual('b', actual[1][0])
        self.assertEqual(2, actual[1][1])
        self.assertEqual('c', actual[2][0])
        self.assertEqual(3, actual[2][1])
        self.assertEqual('d', actual[3][0])
        self.assertEqual(4, actual[3][1])
        self.assertEqual('e', actual[4][0])
        self.assertEqual(5, actual[4][1])

    async def test_map_downlink_view_get_immediate(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            model = _MapDownlinkModel(client)
            model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            downlink_view._model = model
            # When
            actual = downlink_view.get('a')

        # Then
        self.assertEqual(1, actual)

    async def test_map_downlink_view_get_with_wait(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            downlink_view._initialised.set()
            model = _MapDownlinkModel(client)
            model._synced.set()
            model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            downlink_view._model = model
            # When
            actual = downlink_view.get('d', wait_sync=True)

        # Then
        self.assertEqual(4, actual)

    async def test_map_downlink_view_get_immediate_absent(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            model = _MapDownlinkModel(client)
            downlink_view._model = model
            # When
            actual = downlink_view.get('a')

        # Then
        self.assertEqual(Value.absent(), actual)

    async def test_map_downlink_view_get_with_wait_absent(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            downlink_view._initialised.set()
            model = _MapDownlinkModel(client)
            model._synced.set()
            downlink_view._model = model
            # When
            actual = downlink_view.get('d', wait_sync=True)

        # Then
        self.assertEqual(Value.absent(), actual)

    @patch('warnings.warn')
    async def test_map_downlink_view_get_before_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            # When
            downlink_view.get('a')

        # Then
        self.assertEqual('Cannot execute "get" before the downlink has been opened!', mock_warn.call_args_list[0][0][0])

    async def test_map_downlink_view_get_all_immediate(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            model = _MapDownlinkModel(client)
            model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            downlink_view._model = model
            # When
            actual = downlink_view.get_all()

        # Then
        self.assertEqual('a', actual[0][0])
        self.assertEqual(1, actual[0][1])
        self.assertEqual('b', actual[1][0])
        self.assertEqual(2, actual[1][1])
        self.assertEqual('c', actual[2][0])
        self.assertEqual(3, actual[2][1])
        self.assertEqual('d', actual[3][0])
        self.assertEqual(4, actual[3][1])
        self.assertEqual('e', actual[4][0])
        self.assertEqual(5, actual[4][1])

    async def test_map_downlink_view_get_all_with_wait(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            downlink_view._initialised.set()
            model = _MapDownlinkModel(client)
            model._synced.set()
            model._map = {'a': ('a', 1), 'b': ('b', 2), 'c': ('c', 3), 'd': ('d', 4), 'e': ('e', 5)}
            downlink_view._model = model
            # When
            actual = downlink_view.get_all(wait_sync=True)

        # Then
        self.assertEqual('a', actual[0][0])
        self.assertEqual(1, actual[0][1])
        self.assertEqual('b', actual[1][0])
        self.assertEqual(2, actual[1][1])
        self.assertEqual('c', actual[2][0])
        self.assertEqual(3, actual[2][1])
        self.assertEqual('d', actual[3][0])
        self.assertEqual(4, actual[3][1])
        self.assertEqual('e', actual[4][0])
        self.assertEqual(5, actual[4][1])

    async def test_map_downlink_view_get_all_immediate_absent(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            model = _MapDownlinkModel(client)
            downlink_view._model = model
            # When
            actual = downlink_view.get_all()

        # Then
        self.assertEqual([], actual)

    async def test_map_downlink_view_get_all_with_wait_absent(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            downlink_view._is_open = True
            downlink_view._initialised.set()
            model = _MapDownlinkModel(client)
            model._synced.set()
            downlink_view._model = model
            # When
            actual = downlink_view.get_all(wait_sync=True)

        # Then
        self.assertEqual([], actual)

    @patch('warnings.warn')
    async def test_map_downlink_view_get_all_before_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            # When
            downlink_view.get_all()

        # Then
        self.assertEqual('Cannot execute "get_all" before the downlink has been opened!',
                         mock_warn.call_args_list[0][0][0])

    @patch('concurrent.futures._base.Future.result')
    async def test_map_downlink_view_put_blocking(self, mock_result):
        # Given
        with SwimClient() as client:
            node_uri = 'map_node_uri'
            lane_uri = 'map_lane_uri'
            model = _MapDownlinkModel(client)
            mock_connection = MockConnection()
            model.connection = mock_connection
            model.linked.set()
            downlink_view = _MapDownlinkView(client)
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            downlink_view._is_open = True
            downlink_view._initialised.set()
            downlink_view._model = model
            # When
            downlink_view.put('map_key', 'map_value', blocking=True)

        # Then
        self.assertEqual('@command(node:map_node_uri,lane:map_lane_uri)@update(key:map_key)map_value',
                         mock_connection.messages_sent[0])
        self.assertTrue(mock_result.called)

    @patch('concurrent.futures._base.Future.result')
    async def test_map_downlink_view_put_non_blocking(self, mock_result):
        # Given
        with SwimClient() as client:
            node_uri = 'node_map'
            lane_uri = 'lane_map'
            model = _MapDownlinkModel(client)
            mock_connection = MockConnection()
            model.connection = mock_connection
            model.linked.set()
            downlink_view = _MapDownlinkView(client)
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            downlink_view._is_open = True
            downlink_view._initialised.set()
            downlink_view._model = model
            # When
            downlink_view.put('key_map', 'value_map')

        # Then
        self.assertEqual('@command(node:node_map,lane:lane_map)@update(key:key_map)value_map',
                         mock_connection.messages_sent[0])
        self.assertFalse(mock_result.called)

    @patch('warnings.warn')
    async def test_map_downlink_view_put_before_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            # When
            downlink_view.put('key_map', 'value_map')

        # Then
        self.assertEqual('Cannot execute "put" before the downlink has been opened!',
                         mock_warn.call_args_list[0][0][0])

    @patch('concurrent.futures._base.Future.result')
    async def test_map_downlink_view_remove_blocking(self, mock_result):
        # Given
        with SwimClient() as client:
            node_uri = 'map_remove_node_uri'
            lane_uri = 'map_remove_lane_uri'
            model = _MapDownlinkModel(client)
            mock_connection = MockConnection()
            model.connection = mock_connection
            model.linked.set()
            downlink_view = _MapDownlinkView(client)
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            downlink_view._is_open = True
            downlink_view._initialised.set()
            downlink_view._model = model
            # When
            downlink_view.remove('map_remove_key', blocking=True)

        # Then
        self.assertEqual('@command(node:map_remove_node_uri,lane:map_remove_lane_uri)@remove(key:map_remove_key)',
                         mock_connection.messages_sent[0])
        self.assertTrue(mock_result.called)

    @patch('concurrent.futures._base.Future.result')
    async def test_map_downlink_view_remove_non_blocking(self, mock_result):
        # Given
        with SwimClient() as client:
            node_uri = 'node_uri_remove_map'
            lane_uri = 'lane_uri_remove_map'
            model = _MapDownlinkModel(client)
            mock_connection = MockConnection()
            model.connection = mock_connection
            model.linked.set()
            downlink_view = _MapDownlinkView(client)
            downlink_view._node_uri = node_uri
            downlink_view._lane_uri = lane_uri
            downlink_view._is_open = True
            downlink_view._initialised.set()
            downlink_view._model = model
            # When
            downlink_view.remove('remove_key_map')

        # Then
        self.assertEqual('@command(node:node_uri_remove_map,lane:lane_uri_remove_map)@remove(key:remove_key_map)',
                         mock_connection.messages_sent[0])
        self.assertFalse(mock_result.called)

    @patch('warnings.warn')
    async def test_map_downlink_view_remove_before_open(self, mock_warn):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            # When
            downlink_view.remove('key_map_remove')

        # Then
        self.assertEqual('Cannot execute "remove" before the downlink has been opened!',
                         mock_warn.call_args_list[0][0][0])

    async def test_map_downlink_view_execute_did_update(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            mock_did_update = MockDidUpdateCallback()
            downlink_view._did_update_callback = mock_did_update.execute
            key = 'Test_update_key'
            new_value = 'Test_update_new_value'
            old_value = 'Test_update_old_value'
            # When
            await downlink_view._execute_did_update(key, new_value, old_value)
            while not mock_did_update.called:
                pass
        # Then
        self.assertEqual(key, mock_did_update.key)
        self.assertEqual(new_value, mock_did_update.new_value)
        self.assertEqual(old_value, mock_did_update.old_value)

    async def test_map_downlink_view_execute_did_update_no_callback(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            key = 'Test_update_key'
            new_value = 'Test_update_new_value'
            old_value = 'Test_update_old_value'
            # When
            with patch('swimos.SwimClient._schedule_task') as mock_schedule_task:
                await downlink_view._execute_did_update(key, new_value, old_value)

        # Then
        self.assertFalse(mock_schedule_task.called)

    async def test_map_downlink_view_execute_did_remove(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            mock_did_remove = MockDidRemoveCallback()
            downlink_view._did_remove_callback = mock_did_remove.execute
            key = 'Test_remove_key'
            value = 'Test_remove_value'
            # When
            await downlink_view._execute_did_remove(key, value)
            while not mock_did_remove.called:
                pass
        # Then
        self.assertEqual(key, mock_did_remove.key)
        self.assertEqual(value, mock_did_remove.value)

    async def test_map_downlink_view_execute_did_remove_no_callback(self):
        # Given
        with SwimClient() as client:
            downlink_view = _MapDownlinkView(client)
            key = 'Test_remove_key'
            value = 'Test_remove_value'
            # When
            with patch('swimos.SwimClient._schedule_task') as mock_schedule_task:
                await downlink_view._execute_did_remove(key, value)

        # Then
        self.assertFalse(mock_schedule_task.called)

    async def test_map_downlink_view_did_update_valid(self):
        # Given
        client = SwimClient()
        downlink_view = _MapDownlinkView(client)
        function = mock_did_update_callback
        # When
        downlink_view.did_update(function)
        # Then
        self.assertTrue(function, downlink_view._did_update_callback)

    async def test_map_downlink_view_did_update_invalid(self):
        # Given
        client = SwimClient()
        downlink_view = _MapDownlinkView(client)
        function = 111
        # When
        with self.assertRaises(TypeError) as error:
            # noinspection PyTypeChecker
            downlink_view.did_update(function)

        # Then
        message = error.exception.args[0]
        self.assertEqual(message, 'Callback must be a coroutine or a function!')

    async def test_map_downlink_view_did_remove_valid(self):
        # Given
        client = SwimClient()
        downlink_view = _MapDownlinkView(client)
        function = mock_did_remove_callback
        # When
        downlink_view.did_remove(function)
        # Then
        self.assertTrue(function, downlink_view._did_remove_callback)

    async def test_map_downlink_view_did_remove_invalid(self):
        # Given
        client = SwimClient()
        downlink_view = _MapDownlinkView(client)
        function = 111
        # When
        with self.assertRaises(TypeError) as error:
            # noinspection PyTypeChecker
            downlink_view.did_remove(function)

        # Then
        message = error.exception.args[0]
        self.assertEqual(message, 'Callback must be a coroutine or a function!')
