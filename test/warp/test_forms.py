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

import math
import unittest

from swimos.structures import Value, Text, RecordMap, Slot, Attr, Num
from swimos.warp._warp import _SyncedResponseForm, _SyncedResponse, _SyncRequestForm, _SyncRequest, _LinkedResponseForm, \
    _CommandMessageForm, _EventMessageForm, _LinkedResponse, _CommandMessage, _EventMessage, _LinkRequestForm, \
    _LinkRequest, _UnlinkedResponseForm, _UnlinkedResponse


class TestForms(unittest.TestCase):

    def test_lane_addressed_form_mold_empty(self):
        # Given
        envelope = None
        form = _SyncedResponseForm()
        # When
        actual = form._mold(envelope)
        # Then
        self.assertEqual(Value.extant(), actual)

    def test_lane_addressed_form_cast_missing_headers(self):
        # Given
        form = _SyncedResponseForm()
        items = RecordMap.create()
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('synced'), items))
        # When
        actual = form._cast(record_map)
        # Then
        self.assertEqual(None, actual)

    def test_lane_addressed_form_cast_missing_node(self):
        # Given
        form = _SyncedResponseForm()
        items = RecordMap.create()
        items.add(Attr.create_attr(Text.create_from('lane'), Text.create_from('foo_lane')))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('synced'), items))
        # When
        actual = form._cast(record_map)
        # Then
        self.assertEqual(None, actual)

    def test_lane_addressed_form_cast_missing_lane(self):
        # Given
        form = _SyncedResponseForm()
        items = RecordMap.create()
        items.add(Attr.create_attr(Text.create_from('node'), Text.create_from('foo_node')))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('synced'), items))
        # When
        actual = form._cast(record_map)
        # Then
        self.assertEqual(None, actual)

    def test_link_addressed_form_mold_empty(self):
        # Given
        envelope = None
        form = _SyncRequestForm()
        # When
        actual = form._mold(envelope)
        # Then
        self.assertEqual(Value.extant(), actual)

    def test_link_addressed_form_mold_prio_zero(self):
        # Given
        envelope = _SyncRequest('node_foo', 'lane_bar', prio=0, rate=2.5)
        form = _SyncRequestForm()
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual('node_foo', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('lane_bar', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('rate', actual.get_item(0).value.get_item(2).key.value)
        self.assertEqual(2.5, actual.get_item(0).value.get_item(2).value.value)

    def test_link_addressed_form_mold_prio_nan(self):
        # Given
        envelope = _SyncRequest('synced_node', 'synced_lane', prio=math.nan, rate=3.4)
        form = _SyncRequestForm()
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual('synced_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('synced_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('rate', actual.get_item(0).value.get_item(2).key.value)
        self.assertEqual(3.4, actual.get_item(0).value.get_item(2).value.value)

    def test_link_addressed_form_mold_rate_zero(self):
        # Given
        envelope = _SyncRequest('node_rate_foo', 'lane_rate_bar', prio=2.1, rate=0)
        form = _SyncRequestForm()
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual('node_rate_foo', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('lane_rate_bar', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('prio', actual.get_item(0).value.get_item(2).key.value)
        self.assertEqual(2.1, actual.get_item(0).value.get_item(2).value.value)

    def test_link_addressed_form_mold_rate_nan(self):
        # Given
        envelope = _SyncRequest('node_baz', 'lane_qux', prio=13.4, rate=math.nan)
        form = _SyncRequestForm()
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual('node_baz', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('lane_qux', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('prio', actual.get_item(0).value.get_item(2).key.value)
        self.assertEqual(13.4, actual.get_item(0).value.get_item(2).value.value)

    def test_link_addressed_cast_missing_headers(self):
        # Given
        form = _SyncRequestForm()
        items = RecordMap.create()
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('sync'), items))
        # When
        actual = form._cast(record_map)
        # Then
        self.assertEqual(None, actual)

    def test_link_addressed_form_cast_missing_node(self):
        # Given
        form = _SyncRequestForm()
        items = RecordMap.create()
        items.add(Attr.create_attr(Text.create_from('lane'), Text.create_from('sync_foo_lane')))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('sync'), items))
        # When
        actual = form._cast(record_map)
        # Then
        self.assertEqual(None, actual)

    def test_link_addressed_form_cast_missing_lane(self):
        # Given
        form = _SyncRequestForm()
        items = RecordMap.create()
        items.add(Attr.create_attr(Text.create_from('node'), Text.create_from('sync_foo_node')))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('sync'), items))
        # When
        actual = form._cast(record_map)
        # Then
        self.assertEqual(None, actual)

    def test_synced_form(self):
        # Given
        actual = _SyncedResponseForm()
        # Then
        self.assertIsInstance(actual, _SyncedResponseForm)
        self.assertEqual('synced', actual._tag)

    def test_synced_form_create_envelope(self):
        # Given
        form = _SyncedResponseForm()
        body = Text.create_from('synced_body')
        # When
        actual = form._create_envelope_from('foo', 'bar', body)
        # Then
        self.assertIsInstance(actual, _SyncedResponse)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(body, actual._body)

    def test_synced_form_mold(self):
        # Given
        form = _SyncedResponseForm()
        envelope = _SyncedResponse('foo_node', 'bar_lane', body=Text.create_from('Boo'))
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('bar_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('Boo', actual.get_item(1).value)

    def test_synced_form_cast(self):
        # Given
        form = _SyncedResponseForm()
        items = RecordMap.create()
        items.add(Slot.create_slot(Text.create_from('node'), Text.create_from('synced_node')))
        items.add(Slot.create_slot(Text.create_from('lane'), Text.create_from('synced_lane')))
        body = Attr.create_attr(Text.create_from('body'), Text.create_from('synced_body'))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('synced'), items))
        record_map.add(body)
        # When
        actual = form._cast(record_map)
        # Then
        self.assertIsInstance(actual, _SyncedResponse)
        self.assertEqual('synced_node', actual._node_uri)
        self.assertEqual('synced_lane', actual._lane_uri)
        self.assertEqual(body, actual._body.get_item(0))

    def test_sync_form(self):
        # Given
        actual = _SyncRequestForm()
        # Then
        self.assertIsInstance(actual, _SyncRequestForm)
        self.assertEqual('sync', actual._tag)

    def test_sync_form_create_envelope(self):
        # Given
        form = _SyncRequestForm()
        body = Text.create_from('sync_body')
        # When
        actual = form._create_envelope_from('foo', 'bar', prio=3.2, rate=2.1, body=body)
        # Then
        self.assertIsInstance(actual, _SyncRequest)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(3.2, actual._prio)
        self.assertEqual(2.1, actual._rate)
        self.assertEqual(body, actual._body)

    def test_sync_form_mold(self):
        # Given
        form = _SyncRequestForm()
        envelope = _SyncRequest('sync_node', 'sync_lane', prio=99.1, rate=41.42, body=Text.create_from('Moo'))
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('sync', actual._tag)
        self.assertEqual('sync_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('sync_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual(99.1, actual.get_item(0).value.get_item(2).value.value)
        self.assertEqual(41.42, actual.get_item(0).value.get_item(3).value.value)
        self.assertEqual('Moo', actual.get_item(1).value)

    def test_sync_form_cast(self):
        # Given
        form = _SyncRequestForm()
        items = RecordMap.create()
        items.add(Slot.create_slot(Text.create_from('node'), Text.create_from('sync_node')))
        items.add(Slot.create_slot(Text.create_from('lane'), Text.create_from('sync_lane')))
        items.add(Slot.create_slot(Text.create_from('prio'), Num.create_from(33.12)))
        items.add(Slot.create_slot(Text.create_from('rate'), Num.create_from(12.33)))
        body = Attr.create_attr(Text.create_from('body'), Text.create_from('sync_body'))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('sync'), items))
        record_map.add(body)
        # When
        actual = form._cast(record_map)
        # Then
        self.assertIsInstance(actual, _SyncRequest)
        self.assertEqual('sync_node', actual._node_uri)
        self.assertEqual('sync_lane', actual._lane_uri)
        self.assertEqual(33.12, actual._prio)
        self.assertEqual(12.33, actual._rate)
        self.assertEqual(body, actual._body.get_item(0))

    def test_link_form(self):
        # Given
        actual = _LinkRequestForm()
        # Then
        self.assertIsInstance(actual, _LinkRequestForm)
        self.assertEqual('link', actual._tag)

    def test_link_form_create_envelope(self):
        # Given
        form = _LinkRequestForm()
        body = Text.create_from('link_body')
        # When
        actual = form._create_envelope_from('moo', 'cow', prio=0.13, rate=0.26, body=body)
        # Then
        self.assertIsInstance(actual, _LinkRequest)
        self.assertEqual('moo', actual._node_uri)
        self.assertEqual('cow', actual._lane_uri)
        self.assertEqual(0.13, actual._prio)
        self.assertEqual(0.26, actual._rate)
        self.assertEqual(body, actual._body)

    def test_link_form_mold(self):
        # Given
        form = _LinkRequestForm()
        envelope = _LinkRequest('link_node', 'link_lane', prio=1, rate=2, body=Text.create_from('Moo'))
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('link', actual._tag)
        self.assertEqual('link_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('link_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual(1, actual.get_item(0).value.get_item(2).value.value)
        self.assertEqual(2, actual.get_item(0).value.get_item(3).value.value)
        self.assertEqual('Moo', actual.get_item(1).value)

    def test_link_form_cast(self):
        # Given
        form = _LinkRequestForm()
        items = RecordMap.create()
        items.add(Slot.create_slot(Text.create_from('node'), Text.create_from('link_node')))
        items.add(Slot.create_slot(Text.create_from('lane'), Text.create_from('link_lane')))
        items.add(Slot.create_slot(Text.create_from('prio'), Num.create_from(1)))
        items.add(Slot.create_slot(Text.create_from('rate'), Num.create_from(3)))
        body = Attr.create_attr(Text.create_from('body'), Text.create_from('link_body'))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('link'), items))
        record_map.add(body)
        # When
        actual = form._cast(record_map)
        # Then
        self.assertIsInstance(actual, _LinkRequest)
        self.assertEqual('link_node', actual._node_uri)
        self.assertEqual('link_lane', actual._lane_uri)
        self.assertEqual(1, actual._prio)
        self.assertEqual(3, actual._rate)
        self.assertEqual(body, actual._body.get_item(0))

    def test_linked_form(self):
        # Given
        actual = _LinkedResponseForm()
        # Then
        self.assertIsInstance(actual, _LinkedResponseForm)
        self.assertEqual('linked', actual._tag)

    def test_linked_form_create_envelope(self):
        # Given
        form = _LinkedResponseForm()
        body = Text.create_from('linked_body')
        # When
        actual = form._create_envelope_from('boo', 'far', prio=1.13, rate=2.26, body=body)
        # Then
        self.assertIsInstance(actual, _LinkedResponse)
        self.assertEqual('boo', actual._node_uri)
        self.assertEqual('far', actual._lane_uri)
        self.assertEqual(1.13, actual._prio)
        self.assertEqual(2.26, actual._rate)
        self.assertEqual(body, actual._body)

    def test_linked_form_mold(self):
        # Given
        form = _LinkedResponseForm()
        envelope = _LinkedResponse('linked_node', 'linked_lane', prio=13, rate=15, body=Text.create_from('Foo'))
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('linked', actual._tag)
        self.assertEqual('linked_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('linked_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual(13, actual.get_item(0).value.get_item(2).value.value)
        self.assertEqual(15, actual.get_item(0).value.get_item(3).value.value)
        self.assertEqual('Foo', actual.get_item(1).value)

    def test_linked_form_cast(self):
        # Given
        form = _LinkedResponseForm()
        items = RecordMap.create()
        items.add(Slot.create_slot(Text.create_from('node'), Text.create_from('linked_node')))
        items.add(Slot.create_slot(Text.create_from('lane'), Text.create_from('linked_lane')))
        items.add(Slot.create_slot(Text.create_from('prio'), Num.create_from(14)))
        items.add(Slot.create_slot(Text.create_from('rate'), Num.create_from(13)))
        body = Attr.create_attr(Text.create_from('body'), Text.create_from('linked_body'))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('linked'), items))
        record_map.add(body)
        # When
        actual = form._cast(record_map)
        # Then
        self.assertIsInstance(actual, _LinkedResponse)
        self.assertEqual('linked_node', actual._node_uri)
        self.assertEqual('linked_lane', actual._lane_uri)
        self.assertEqual(14, actual._prio)
        self.assertEqual(13, actual._rate)
        self.assertEqual(body, actual._body.get_item(0))

    def test_unlinked_form(self):
        # Given
        actual = _UnlinkedResponseForm()
        # Then
        self.assertIsInstance(actual, _UnlinkedResponseForm)
        self.assertEqual('unlinked', actual._tag)

    def test_unlinked_form_create_envelope(self):
        # Given
        form = _UnlinkedResponseForm()
        body = Text.create_from('unlinked_body')
        # When
        actual = form._create_envelope_from('oof', 'bar', prio=2, rate=6, body=body)
        # Then
        self.assertIsInstance(actual, _UnlinkedResponse)
        self.assertEqual('oof', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(2, actual._prio)
        self.assertEqual(6, actual._rate)
        self.assertEqual(body, actual._body)

    def test_unlinked_form_mold(self):
        # Given
        form = _UnlinkedResponseForm()
        envelope = _LinkedResponse('unlinked_node', 'unlinked_lane', prio=9, rate=10, body=Text.create_from('Baz'))
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('unlinked_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('unlinked_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual(9, actual.get_item(0).value.get_item(2).value.value)
        self.assertEqual(10, actual.get_item(0).value.get_item(3).value.value)
        self.assertEqual('Baz', actual.get_item(1).value)

    def test_unlinked_form_cast(self):
        # Given
        form = _UnlinkedResponseForm()
        items = RecordMap.create()
        items.add(Slot.create_slot(Text.create_from('node'), Text.create_from('unlinked_node')))
        items.add(Slot.create_slot(Text.create_from('lane'), Text.create_from('unlinked_lane')))
        items.add(Slot.create_slot(Text.create_from('prio'), Num.create_from(20)))
        items.add(Slot.create_slot(Text.create_from('rate'), Num.create_from(25)))
        body = Attr.create_attr(Text.create_from('body'), Text.create_from('unlinked_body'))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('unlinked'), items))
        record_map.add(body)
        # When
        actual = form._cast(record_map)
        # Then
        self.assertIsInstance(actual, _UnlinkedResponse)
        self.assertEqual('unlinked_node', actual._node_uri)
        self.assertEqual('unlinked_lane', actual._lane_uri)
        self.assertEqual(20, actual._prio)
        self.assertEqual(25, actual._rate)
        self.assertEqual(body, actual._body.get_item(0))

    def test_command_form(self):
        # Given
        actual = _CommandMessageForm()
        # Then
        self.assertIsInstance(actual, _CommandMessageForm)
        self.assertEqual('command', actual._tag)

    def test_command_form_create_envelope(self):
        # Given
        form = _CommandMessageForm()
        body = Text.create_from('message_body')
        # When
        actual = form._create_envelope_from('message_foo', 'message_bar', body=body)
        # Then
        self.assertIsInstance(actual, _CommandMessage)
        self.assertEqual('message_foo', actual._node_uri)
        self.assertEqual('message_bar', actual._lane_uri)
        self.assertEqual(body, actual._body)

    def test_command_form_mold(self):
        # Given
        form = _CommandMessageForm()
        envelope = _CommandMessage('command_node', 'command_lane', body=Text.create_from('Command_body'))
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('command', actual._tag)
        self.assertEqual('command_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('command_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('Command_body', actual.get_item(1).value)

    def test_command_form_cast(self):
        # Given
        form = _CommandMessageForm()
        items = RecordMap.create()
        items.add(Slot.create_slot(Text.create_from('node'), Text.create_from('command_node')))
        items.add(Slot.create_slot(Text.create_from('lane'), Text.create_from('command_lane')))
        body = Attr.create_attr(Text.create_from('body'), Text.create_from('command_body'))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('command'), items))
        record_map.add(body)
        # When
        actual = form._cast(record_map)
        # Then
        self.assertIsInstance(actual, _CommandMessage)
        self.assertEqual('command_node', actual._node_uri)
        self.assertEqual('command_lane', actual._lane_uri)
        self.assertEqual(body, actual._body.get_item(0))

    def test_event_form(self):
        # Given
        actual = _EventMessageForm()
        # Then
        self.assertIsInstance(actual, _EventMessageForm)
        self.assertEqual('event', actual._tag)

    def test_event_form_create_envelope(self):
        # Given
        form = _EventMessageForm()
        body = Text.create_from('event_body')
        # When
        actual = form._create_envelope_from('event_foo', 'event_bar', body=body)
        # Then
        self.assertIsInstance(actual, _EventMessage)
        self.assertEqual('event_foo', actual._node_uri)
        self.assertEqual('event_bar', actual._lane_uri)
        self.assertEqual(body, actual._body)

    def test_event_form_mold(self):
        # Given
        form = _EventMessageForm()
        envelope = _EventMessage('event_node', 'event_lane', body=Text.create_from('Event_body'))
        # When
        actual = form._mold(envelope)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('event', actual._tag)
        self.assertEqual('event_node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('event_lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('Event_body', actual.get_item(1).value)

    def test_event_form_cast(self):
        # Given
        form = _EventMessageForm()
        items = RecordMap.create()
        items.add(Slot.create_slot(Text.create_from('node'), Text.create_from('event_node')))
        items.add(Slot.create_slot(Text.create_from('lane'), Text.create_from('event_lane')))
        body = Attr.create_attr(Text.create_from('body'), Text.create_from('event_body'))
        record_map = RecordMap.create()
        record_map.add(Attr.create_attr(Text.create_from('event'), items))
        record_map.add(body)
        # When
        actual = form._cast(record_map)
        # Then
        self.assertIsInstance(actual, _EventMessage)
        self.assertEqual('event_node', actual._node_uri)
        self.assertEqual('event_lane', actual._lane_uri)
        self.assertEqual(body, actual._body.get_item(0))
