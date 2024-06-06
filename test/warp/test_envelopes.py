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

import unittest

from swimos.structures import Text
from swimos.structures._structs import _Absent
from swimos.warp._warp import _Envelope, _SyncRequestForm, _SyncedResponseForm, _LinkedResponseForm, _EventMessageForm, \
    _CommandMessageForm, _SyncRequest, _SyncedResponse, _LinkedResponse, _CommandMessage, _EventMessage, _LinkRequestForm, \
    _UnlinkedResponseForm, _LinkRequest, _UnlinkedResponse


class TestEnvelopes(unittest.TestCase):

    def test_resolve_form_sync(self):
        # Given
        tag = 'sync'
        # When
        actual = _Envelope._resolve_form(tag)
        # Then
        self.assertIsInstance(actual, _SyncRequestForm)

    def test_resolve_form_synced(self):
        # Given
        tag = 'synced'
        # When
        actual = _Envelope._resolve_form(tag)
        # Then
        self.assertIsInstance(actual, _SyncedResponseForm)

    def test_resolve_form_link(self):
        # Given
        tag = 'link'
        # When
        actual = _Envelope._resolve_form(tag)
        # Then
        self.assertIsInstance(actual, _LinkRequestForm)

    def test_resolve_form_linked(self):
        # Given
        tag = 'linked'
        # When
        actual = _Envelope._resolve_form(tag)
        # Then
        self.assertIsInstance(actual, _LinkedResponseForm)

    def test_resolve_form_unlinked(self):
        # Given
        tag = 'unlinked'
        # When
        actual = _Envelope._resolve_form(tag)
        # Then
        self.assertIsInstance(actual, _UnlinkedResponseForm)

    def test_resolve_form_event(self):
        # Given
        tag = 'event'
        # When
        actual = _Envelope._resolve_form(tag)
        # Then
        self.assertIsInstance(actual, _EventMessageForm)

    def test_resolve_form_command(self):
        # Given
        tag = 'command'
        # When
        actual = _Envelope._resolve_form(tag)
        # Then
        self.assertIsInstance(actual, _CommandMessageForm)

    def test_resolve_form_invalid(self):
        # Given
        tag = 'this_is_not_a_valid_form'
        # When
        with self.assertRaises(TypeError) as error:
            _Envelope._resolve_form(tag)
        # Then
        message = error.exception.args[0]
        self.assertEqual(message, 'Invalid form tag: this_is_not_a_valid_form')

    def test_sync_request_empty_body(self):
        # Given
        node_uri = 'foo__sync_node'
        lane_uri = 'bar__sync_lane'
        # When
        actual = _SyncRequest(node_uri, lane_uri)
        # Then
        self.assertEqual('foo__sync_node', actual._node_uri)
        self.assertEqual('bar__sync_lane', actual._lane_uri)
        self.assertEqual(0.0, actual._prio)
        self.assertEqual(0.0, actual._rate)
        self.assertEqual('sync', actual._tag)
        self.assertEqual('foo__sync_node/bar__sync_lane', actual._route)
        self.assertEqual(_Absent._get_absent(), actual._body)
        self.assertIsInstance(actual._form, _SyncRequestForm)

    def test_sync_request_existing_body(self):
        # Given
        node_uri = 'foo_sync_node'
        lane_uri = 'bar_sync_lane'
        body = Text.create_from('Sync_Body')
        priority = 3.5
        rate = 2.0
        # When
        actual = _SyncRequest(node_uri, lane_uri, priority, rate, body=body)
        # Then
        self.assertEqual('foo_sync_node', actual._node_uri)
        self.assertEqual('bar_sync_lane', actual._lane_uri)
        self.assertEqual(3.5, actual._prio)
        self.assertEqual(2.0, actual._rate)
        self.assertEqual('sync', actual._tag)
        self.assertEqual('foo_sync_node/bar_sync_lane', actual._route)
        self.assertEqual(body, actual._body)
        self.assertIsInstance(actual._form, _SyncRequestForm)

    def test_synced_response_empty_body(self):
        # Given
        node_uri = 'foo_synced_node'
        lane_uri = 'bar_synced_lane'
        # When
        actual = _SyncedResponse(node_uri, lane_uri)
        # Then
        self.assertEqual('foo_synced_node', actual._node_uri)
        self.assertEqual('bar_synced_lane', actual._lane_uri)
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo_synced_node/bar_synced_lane', actual._route)
        self.assertEqual(_Absent._get_absent(), actual._body)
        self.assertIsInstance(actual._form, _SyncedResponseForm)

    def test_synced_response_existing_body(self):
        # Given
        node_uri = 'foo_synced_node'
        lane_uri = 'bar_synced_lane'
        body = Text.create_from('Synced_Body')
        # When
        actual = _SyncedResponse(node_uri, lane_uri, body=body)
        # Then
        self.assertEqual('foo_synced_node', actual._node_uri)
        self.assertEqual('bar_synced_lane', actual._lane_uri)
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo_synced_node/bar_synced_lane', actual._route)
        self.assertEqual(body, actual._body)
        self.assertIsInstance(actual._form, _SyncedResponseForm)

    def test_link_request_empty_body(self):
        # Given
        node_uri = 'foo_link_node'
        lane_uri = 'bar_link_lane'
        # When
        actual = _LinkRequest(node_uri, lane_uri)
        # Then
        self.assertEqual('foo_link_node', actual._node_uri)
        self.assertEqual('bar_link_lane', actual._lane_uri)
        self.assertEqual('link', actual._tag)
        self.assertEqual('foo_link_node/bar_link_lane', actual._route)
        self.assertEqual(_Absent._get_absent(), actual._body)
        self.assertIsInstance(actual._form, _LinkRequestForm)

    def test_link_request_existing_body(self):
        # Given
        node_uri = 'foo_link_node'
        lane_uri = 'bar_link_lane'
        body = Text.create_from('Link_Body')
        priority = 13.1
        rate = 11.3
        # When
        actual = _LinkRequest(node_uri, lane_uri, priority, rate, body)
        # Then
        self.assertEqual('foo_link_node', actual._node_uri)
        self.assertEqual('bar_link_lane', actual._lane_uri)
        self.assertEqual('link', actual._tag)
        self.assertEqual('foo_link_node/bar_link_lane', actual._route)
        self.assertEqual(body, actual._body)
        self.assertIsInstance(actual._form, _LinkRequestForm)

    def test_linked_response_empty_body(self):
        # Given
        node_uri = 'foo_linked_node'
        lane_uri = 'bar_linked_lane'
        # When
        actual = _LinkedResponse(node_uri, lane_uri)
        # Then
        self.assertEqual('foo_linked_node', actual._node_uri)
        self.assertEqual('bar_linked_lane', actual._lane_uri)
        self.assertEqual('linked', actual._tag)
        self.assertEqual('foo_linked_node/bar_linked_lane', actual._route)
        self.assertEqual(_Absent._get_absent(), actual._body)
        self.assertIsInstance(actual._form, _LinkedResponseForm)

    def test_linked_response_existing_body(self):
        # Given
        node_uri = 'foo_linked_node'
        lane_uri = 'bar_linked_lane'
        body = Text.create_from('Linked_Body')
        priority = 1.13
        rate = 3.11
        # When
        actual = _LinkedResponse(node_uri, lane_uri, priority, rate, body)
        # Then
        self.assertEqual('foo_linked_node', actual._node_uri)
        self.assertEqual('bar_linked_lane', actual._lane_uri)
        self.assertEqual('linked', actual._tag)
        self.assertEqual('foo_linked_node/bar_linked_lane', actual._route)
        self.assertEqual(body, actual._body)
        self.assertIsInstance(actual._form, _LinkedResponseForm)

    def test_unlinked_response_empty_body(self):
        # Given
        node_uri = 'foo_unlinked_node'
        lane_uri = 'bar_unlinked_lane'
        # When
        actual = _UnlinkedResponse(node_uri, lane_uri)
        # Then
        self.assertEqual('foo_unlinked_node', actual._node_uri)
        self.assertEqual('bar_unlinked_lane', actual._lane_uri)
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('foo_unlinked_node/bar_unlinked_lane', actual._route)
        self.assertEqual(_Absent._get_absent(), actual._body)
        self.assertIsInstance(actual._form, _UnlinkedResponseForm)

    def test_unlinked_response_existing_body(self):
        # Given
        node_uri = 'foo_unlinked_node'
        lane_uri = 'bar_unlinked_lane'
        body = Text.create_from('Unlinked_Body')
        priority = 5.11
        rate = 6.13
        # When
        actual = _UnlinkedResponse(node_uri, lane_uri, priority, rate, body)
        # Then
        self.assertEqual('foo_unlinked_node', actual._node_uri)
        self.assertEqual('bar_unlinked_lane', actual._lane_uri)
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('foo_unlinked_node/bar_unlinked_lane', actual._route)
        self.assertEqual(body, actual._body)
        self.assertIsInstance(actual._form, _UnlinkedResponseForm)

    def test_command_message_empty_body(self):
        # Given
        node_uri = 'foo_command_node'
        lane_uri = 'bar_command_lane'
        # When
        actual = _CommandMessage(node_uri, lane_uri)
        # Then
        self.assertEqual('foo_command_node', actual._node_uri)
        self.assertEqual('bar_command_lane', actual._lane_uri)
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo_command_node/bar_command_lane', actual._route)
        self.assertEqual(_Absent._get_absent(), actual._body)
        self.assertIsInstance(actual._form, _CommandMessageForm)

    def test_command_message_existing_body(self):
        # Given
        node_uri = 'foo_command_node'
        lane_uri = 'bar_command_lane'
        body = Text.create_from('Command_Body')
        # When
        actual = _CommandMessage(node_uri, lane_uri, body)
        # Then
        self.assertEqual('foo_command_node', actual._node_uri)
        self.assertEqual('bar_command_lane', actual._lane_uri)
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo_command_node/bar_command_lane', actual._route)
        self.assertEqual(body, actual._body)
        self.assertIsInstance(actual._form, _CommandMessageForm)

    def test_event_message_empty_body(self):
        # Given
        node_uri = 'foo_event_node'
        lane_uri = 'bar_event_lane'
        # When
        actual = _EventMessage(node_uri, lane_uri)
        # Then
        self.assertEqual('foo_event_node', actual._node_uri)
        self.assertEqual('bar_event_lane', actual._lane_uri)
        self.assertEqual('event', actual._tag)
        self.assertEqual('foo_event_node/bar_event_lane', actual._route)
        self.assertEqual(_Absent._get_absent(), actual._body)
        self.assertIsInstance(actual._form, _EventMessageForm)

    def test_event_message_existing_body(self):
        # Given
        node_uri = 'foo_event_node'
        lane_uri = 'bar_event_lane'
        body = Text.create_from('Event_Body')
        # When
        actual = _EventMessage(node_uri, lane_uri, body)
        # Then
        self.assertEqual('foo_event_node', actual._node_uri)
        self.assertEqual('bar_event_lane', actual._lane_uri)
        self.assertEqual('foo_event_node/bar_event_lane', actual._route)
        self.assertEqual('event', actual._tag)
        self.assertEqual(body, actual._body)
        self.assertIsInstance(actual._form, _EventMessageForm)
