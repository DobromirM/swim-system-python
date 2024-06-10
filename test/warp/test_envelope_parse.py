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

from swimos.warp._warp import _Envelope


class TestParser(unittest.TestCase):

    def test_parse_sync(self):
        # Given
        message = '@sync(node: foo, lane: bar)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)

    def test_parse_sync_escaped(self):
        # Given
        message = '@sync(node: "bar/baz/2", lane: "foo/bar")'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)

    def test_parse_sync_body_int(self):
        # Given
        message = '@sync(node: "bar/baz/2", lane: "foo/bar")43'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(43, actual._body.value)

    def test_parse_sync_body_float(self):
        # Given
        message = '@sync(node: "bar/baz/2", lane: "foo/bar")0.31'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(0.31, actual._body.value)

    def test_parse_sync_body_bool(self):
        # Given
        message = '@sync(node: "bar/baz/2", lane: "foo/bar")false'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(False, actual._body.value)

    def test_parse_sync_body_string(self):
        # Given
        message = '@sync(node: "bar/baz/2", lane: "foo/bar")"Hello, World"'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual('Hello, World', actual._body.value)

    def test_parse_sync_prio(self):
        # Given
        message = '@sync(node: foo, lane: bar, prio: 3.2)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(3.2, actual._prio)

    def test_parse_sync_rate(self):
        # Given
        message = '@sync(node: foo, lane: bar, rate: 33)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(33, actual._rate)

    def test_parse_sync_prio_rate(self):
        # Given
        message = '@sync(node: foo, lane: bar, prio: 13, rate: 37)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('sync', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(13, actual._prio)
        self.assertEqual(37, actual._rate)

    def test_parse_synced(self):
        # Given
        message = '@synced(node: foo, lane: bar)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)

    def test_parse_synced_escaped(self):
        # Given
        message = '@synced(node: "foo/bar", lane: "lane/uri/test")'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo/bar', actual._node_uri)
        self.assertEqual('lane/uri/test', actual._lane_uri)

    def test_parse_synced_body_int(self):
        # Given
        message = '@synced(node: foo, lane: bar)33'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(33, actual._body.value)

    def test_parse_synced_body_float(self):
        # Given
        message = '@synced(node: foo, lane: bar)37.13'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(37.13, actual._body.value)

    def test_parse_synced_body_bool(self):
        # Given
        message = '@synced(node: foo, lane: bar)true'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(True, actual._body.value)

    def test_parse_synced_body_string(self):
        # Given
        message = '@synced(node: foo, lane: bar)"Hello, World"'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('synced', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual('Hello, World', actual._body.value)

    def test_parse_link(self):
        # Given
        message = '@link(node: boo, lane: far)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('boo', actual._node_uri)
        self.assertEqual('far', actual._lane_uri)

    def test_parse_link_escaped(self):
        # Given
        message = '@link(node: "bar/baz/5", lane: "foo/baz")'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('bar/baz/5', actual._node_uri)
        self.assertEqual('foo/baz', actual._lane_uri)

    def test_parse_link_body_int(self):
        # Given
        message = '@link(node: "baz/bar/2", lane: "foo/bar")91'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual('baz/bar/2', actual._node_uri)
        self.assertEqual(91, actual._body.value)

    def test_parse_link_body_float(self):
        # Given
        message = '@link(node: "bar/baz/2", lane: "foo/bar")-0.3'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(-0.3, actual._body.value)

    def test_parse_link_body_bool(self):
        # Given
        message = '@link(node: "bar/baz/2", lane: "foo/bar")false'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(False, actual._body.value)

    def test_parse_link_body_string(self):
        # Given
        message = '@link(node: "bar/baz/2", lane: "foo/bar")"Hello, World"'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual('Hello, World', actual._body.value)

    def test_parse_link_prio(self):
        # Given
        message = '@link(node: foo, lane: bar, prio: 1000.3)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(1000.3, actual._prio)

    def test_parse_link_rate(self):
        # Given
        message = '@link(node: "foo", lane: "1/bar/", rate: 33)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('1/bar/', actual._lane_uri)
        self.assertEqual(33, actual._rate)

    def test_parse_link_prio_rate(self):
        # Given
        message = '@link(node: foo, lane: bar, prio: 13, rate: 37)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('link', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(13, actual._prio)
        self.assertEqual(37, actual._rate)

    def test_parse_linked(self):
        # Given
        message = '@linked(node: foo, lane: bar)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)

    def test_parse_linked_escaped(self):
        # Given
        message = '@linked(node: "bar/baz/2", lane: "foo/bar")'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)

    def test_parse_linked_body_int(self):
        # Given
        message = '@linked(node: "bar/baz/2", lane: "foo/bar")9999999'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(9999999, actual._body.value)

    def test_parse_linked_body_float(self):
        # Given
        message = '@linked(node: "bar/baz/2", lane: "foo/bar")-0.00031'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(-0.00031, actual._body.value)

    def test_parse_linked_body_bool(self):
        # Given
        message = '@linked(node: "bar/baz/2", lane: "foo/bar")false'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(False, actual._body.value)

    def test_parse_linked_body_string(self):
        # Given
        message = '@linked(node: "bar/baz/2", lane: "foo/bar")"Hello, World"'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual('Hello, World', actual._body.value)

    def test_parse_linked_prio(self):
        # Given
        message = '@linked(node: foo, lane: bar, prio: 1000.3)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(1000.3, actual._prio)

    def test_parse_linked_rate(self):
        # Given
        message = '@linked(node: "foo", lane: "1/bar/", rate: 33)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('1/bar/', actual._lane_uri)
        self.assertEqual(33, actual._rate)

    def test_parse_linked_prio_rate(self):
        # Given
        message = '@linked(node: foo, lane: bar, prio: 13, rate: 37)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('linked', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(13, actual._prio)
        self.assertEqual(37, actual._rate)

    def test_parse_unlinked(self):
        # Given
        message = '@unlinked(node: foo, lane: bar)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)

    def test_parse_unlinked_escaped(self):
        # Given
        message = '@unlinked(node: "bar/baz/2", lane: "foo/bar")'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)

    def test_parse_unlinked_body_int(self):
        # Given
        message = '@unlinked(node: "bar/baz/2", lane: "foo/bar")9999999'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(9999999, actual._body.value)

    def test_parse_unlinked_body_float(self):
        # Given
        message = '@unlinked(node: "bar/baz/2", lane: "foo/bar")-0.00031'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(-0.00031, actual._body.value)

    def test_parse_unlinked_body_bool(self):
        # Given
        message = '@unlinked(node: "bar/baz/2", lane: "foo/bar")false'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(False, actual._body.value)

    def test_parse_unlinked_body_string(self):
        # Given
        message = '@unlinked(node: "bar/baz/2", lane: "foo/bar")"Hello, World"'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('unlinked', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual('Hello, World', actual._body.value)

    def test_parse_unlinked_prio(self):
        # Given
        message = '@unlinked(node: foo, lane: bar, prio: 1000.3)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(1000.3, actual._prio)

    def test_parse_unlinked_rate(self):
        # Given
        message = '@unlinked(node: "foo", lane: "1/bar/", rate: 33)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('1/bar/', actual._lane_uri)
        self.assertEqual(33, actual._rate)

    def test_parse_unlinked_prio_rate(self):
        # Given
        message = '@unlinked(node: foo, lane: bar, prio: 13, rate: 37)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)
        self.assertEqual(13, actual._prio)
        self.assertEqual(37, actual._rate)

    def test_parse_command(self):
        # Given
        message = '@command(node: foo, lane: bar)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)

    def test_parse_command_escaped(self):
        # Given
        message = '@command(node: "foo/bar", lane: "lane/uri/test")'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo/bar', actual._node_uri)
        self.assertEqual('lane/uri/test', actual._lane_uri)

    def test_parse_command_body_int(self):
        # Given
        message = '@command(node: "foo/bar", lane: "lane/uri/test")-24'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo/bar', actual._node_uri)
        self.assertEqual('lane/uri/test', actual._lane_uri)
        self.assertEqual(-24, actual._body.value)

    def test_parse_command_body_float(self):
        # Given
        message = '@command(node: "foo/bar", lane: "lane/uri/test")-0.5'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo/bar', actual._node_uri)
        self.assertEqual('lane/uri/test', actual._lane_uri)
        self.assertEqual(-0.5, actual._body.value)

    def test_parse_command_body_bool(self):
        # Given
        message = '@command(node: "foo/bar", lane: "lane/uri/test")true'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo/bar', actual._node_uri)
        self.assertEqual('lane/uri/test', actual._lane_uri)
        self.assertEqual(True, actual._body.value)

    def test_parse_command_body_string(self):
        # Given
        message = '@command(node: "foo/bar", lane: "lane/uri/test")"0.32"'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('command', actual._tag)
        self.assertEqual('foo/bar', actual._node_uri)
        self.assertEqual('lane/uri/test', actual._lane_uri)
        self.assertEqual('0.32', actual._body.value)

    def test_parse_command_body_remove(self):
        # Given
        message = '@command(node:"/unit/foo",lane:shoppingCart)@remove(key:FromClientLink)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('command', actual._tag)
        self.assertEqual('/unit/foo', actual._node_uri)
        self.assertEqual('shoppingCart', actual._lane_uri)
        self.assertEqual('remove', actual._body.get_items()[0].key.value)
        self.assertEqual('key', actual._body.get_items()[0].value.get_items()[0].key.value)
        self.assertEqual('FromClientLink', actual._body.get_items()[0].value.get_items()[0].value.value)

    def test_parse_event(self):
        # Given
        message = '@event(node: foo, lane: bar)'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('foo', actual._node_uri)
        self.assertEqual('bar', actual._lane_uri)

    def test_parse_event_escaped(self):
        # Given
        message = '@event(node: "bar/baz/2", lane: "foo/bar")'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)

    def test_parse_event_body_int(self):
        # Given
        message = '@event(node: "bar/baz/2", lane: "foo/bar")332'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(332, actual._body.value)

    def test_parse_event_body_float(self):
        # Given
        message = '@event(node: "bar/baz/2", lane: "foo/bar")0.1'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(0.1, actual._body.value)

    def test_parse_event_body_bool(self):
        # Given
        message = '@event(node: "bar/baz/2", lane: "foo/bar")true'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual(True, actual._body.value)

    def test_parse_event_body_string(self):
        # Given
        message = '@event(node: "bar/baz/2", lane: "foo/bar")"Hello, World"'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)
        self.assertEqual('Hello, World', actual._body.value)

    def test_parse_event_body_object(self):
        # Given
        message = '@event(node: "bar/baz/2", lane: "foo/bar")@Person{name:Bar,age:14,salary:5.9}'
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)

        self.assertEqual(4, len(actual._body.get_items()))
        self.assertEqual('Person', actual._body.get_items()[0].key.value)
        self.assertEqual('name', actual._body.get_items()[1].key.value)
        self.assertEqual('Bar', actual._body.get_items()[1].value.value)
        self.assertEqual('age', actual._body.get_items()[2].key.value)
        self.assertEqual(14, actual._body.get_items()[2].value.value)
        self.assertEqual('salary', actual._body.get_items()[3].key.value)
        self.assertEqual(5.9, actual._body.get_items()[3].value.value)

    def test_parse_event_body_nested(self):
        # Given
        person = '@Person{name:Par,age:11,salary:5.9,friend:@Person{name:Foo,age:18,salary:99.9}'
        message = '@event(node: "bar/baz/2", lane: "foo/bar")' + person
        # When
        actual = _Envelope._parse_recon(message)
        # Then
        self.assertEqual('event', actual._tag)
        self.assertEqual('bar/baz/2', actual._node_uri)
        self.assertEqual('foo/bar', actual._lane_uri)

        self.assertEqual(5, len(actual._body.get_items()))
        self.assertEqual('Person', actual._body.get_items()[0].key.value)
        self.assertEqual('name', actual._body.get_items()[1].key.value)
        self.assertEqual('Par', actual._body.get_items()[1].value.value)
        self.assertEqual('age', actual._body.get_items()[2].key.value)
        self.assertEqual(11, actual._body.get_items()[2].value.value)
        self.assertEqual('salary', actual._body.get_items()[3].key.value)
        self.assertEqual(5.9, actual._body.get_items()[3].value.value)
        self.assertEqual('friend', actual._body.get_items()[4].key.value)
        self.assertEqual(4, len(actual._body.get_items()[4].value.get_items()))
        self.assertEqual('Person', actual._body.get_items()[4].value.get_items()[0].key.value)
        self.assertEqual('name', actual._body.get_items()[4].value.get_items()[1].key.value)
        self.assertEqual('Foo', actual._body.get_items()[4].value.get_items()[1].value.value)
        self.assertEqual('age', actual._body.get_items()[4].value.get_items()[2].key.value)
        self.assertEqual(18, actual._body.get_items()[4].value.get_items()[2].value.value)
        self.assertEqual('salary', actual._body.get_items()[4].value.get_items()[3].key.value)
        self.assertEqual(99.9, actual._body.get_items()[4].value.get_items()[3].value.value)
