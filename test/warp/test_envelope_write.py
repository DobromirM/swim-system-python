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

from swimos.structures import Num, Text, RecordMap, Attr, Slot, Bool
from swimos.structures._structs import _Extant
from swimos.warp._warp import _SyncRequest, _SyncedResponse, _EventMessage, _LinkedResponse, _CommandMessage, \
    _LinkRequest, _UnlinkedResponse


class TestWriters(unittest.TestCase):

    def test_write_sync(self):
        # Given
        envelope = _SyncRequest('foo', 'bar')
        expected = '@sync(node:foo,lane:bar)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_escaped(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar')
        expected = '@sync(node:"bar/baz/",lane:"foo/bar")'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_body_int(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar', body=Num.create_from(42))
        expected = '@sync(node:"bar/baz/",lane:"foo/bar")42'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_body_float(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar', body=Num.create_from(33.22))
        expected = '@sync(node:"bar/baz/",lane:"foo/bar")33.22'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_body_bool(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar', body=Bool.create_from(False))
        expected = '@sync(node:"bar/baz/",lane:"foo/bar")false'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_body_string(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar', body=Text.create_from('Hello, World!'))
        expected = '@sync(node:"bar/baz/",lane:"foo/bar")"Hello, World!"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_prio(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar', prio=33, body=Text.create_from('Hello, World!'))
        expected = '@sync(node:"bar/baz/",lane:"foo/bar",prio:33)"Hello, World!"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_rate(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar', rate=0.3, body=Text.create_from('Hello, World!'))
        expected = '@sync(node:"bar/baz/",lane:"foo/bar",rate:0.3)"Hello, World!"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_sync_prio_rate(self):
        # Given
        envelope = _SyncRequest('bar/baz/', 'foo/bar', prio=33.2, rate=0.3, body=Text.create_from('Hello, World!'))
        expected = '@sync(node:"bar/baz/",lane:"foo/bar",prio:33.2,rate:0.3)"Hello, World!"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_synced(self):
        # Given
        envelope = _SyncedResponse('foo', 'bar')
        expected = '@synced(node:foo,lane:bar)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_synced_escaped(self):
        # Given
        envelope = _SyncedResponse('foo/bar/baz', 'baz/bar/foo')
        expected = '@synced(node:"foo/bar/baz",lane:"baz/bar/foo")'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_synced_body_int(self):
        # Given
        envelope = _SyncedResponse('foo/bar/baz', 'baz/bar/foo', body=Num.create_from(-13))
        expected = '@synced(node:"foo/bar/baz",lane:"baz/bar/foo")-13'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_synced_body_float(self):
        # Given
        envelope = _SyncedResponse('foo/bar/baz', 'baz/bar/foo', body=Num.create_from(-13.04))
        expected = '@synced(node:"foo/bar/baz",lane:"baz/bar/foo")-13.04'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_synced_body_bool(self):
        # Given
        envelope = _SyncedResponse('foo/bar/baz', 'baz/bar/foo', body=Bool.create_from(True))
        expected = '@synced(node:"foo/bar/baz",lane:"baz/bar/foo")true'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_synced_body_string(self):
        # Given
        envelope = _SyncedResponse('foo/bar/baz', 'baz/bar/foo', body=Text.create_from('Hello, friend.'))
        expected = '@synced(node:"foo/bar/baz",lane:"baz/bar/foo")"Hello, friend."'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link(self):
        # Given
        envelope = _LinkRequest('test', 'foo')
        expected = '@link(node:test,lane:foo)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_escaped(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3')
        expected = '@link(node:"/unit/5",lane:"/unit/3")'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_body_int(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3', body=Num.create_from(-100))
        expected = '@link(node:"/unit/5",lane:"/unit/3")-100'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_body_float(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3', body=Num.create_from(-100.0))
        expected = '@link(node:"/unit/5",lane:"/unit/3")-100.0'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_body_bool(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3', body=Bool.create_from(False))
        expected = '@link(node:"/unit/5",lane:"/unit/3")false'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_body_string(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3', body=Text.create_from('spam and \\ham/'))
        expected = '@link(node:"/unit/5",lane:"/unit/3")"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_prio(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3', prio=33.2, body=Text.create_from('spam and \\ham/'))
        expected = '@link(node:"/unit/5",lane:"/unit/3",prio:33.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_rate(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3', rate=0.2, body=Text.create_from('spam and \\ham/'))
        expected = '@link(node:"/unit/5",lane:"/unit/3",rate:0.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_link_prio_rate(self):
        # Given
        envelope = _LinkRequest('/unit/5', '/unit/3', prio=22.11, rate=0.2, body=Text.create_from('spam and \\ham/'))
        expected = '@link(node:"/unit/5",lane:"/unit/3",prio:22.11,rate:0.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked(self):
        # Given
        envelope = _LinkedResponse('test', 'foo')
        expected = '@linked(node:test,lane:foo)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_escaped(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3')
        expected = '@linked(node:"/unit/5",lane:"/unit/3")'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_body_int(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3', body=Num.create_from(-100))
        expected = '@linked(node:"/unit/5",lane:"/unit/3")-100'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_body_float(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3', body=Num.create_from(-100.0))
        expected = '@linked(node:"/unit/5",lane:"/unit/3")-100.0'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_body_bool(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3', body=Bool.create_from(False))
        expected = '@linked(node:"/unit/5",lane:"/unit/3")false'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_body_string(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3', body=Text.create_from('spam and \\ham/'))
        expected = '@linked(node:"/unit/5",lane:"/unit/3")"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_prio(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3', prio=33.2, body=Text.create_from('spam and \\ham/'))
        expected = '@linked(node:"/unit/5",lane:"/unit/3",prio:33.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_rate(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3', rate=0.2, body=Text.create_from('spam and \\ham/'))
        expected = '@linked(node:"/unit/5",lane:"/unit/3",rate:0.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_linked_prio_rate(self):
        # Given
        envelope = _LinkedResponse('/unit/5', '/unit/3', prio=22.11, rate=0.2, body=Text.create_from('spam and \\ham/'))
        expected = '@linked(node:"/unit/5",lane:"/unit/3",prio:22.11,rate:0.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked(self):
        # Given
        envelope = _UnlinkedResponse('test', 'foo')
        expected = '@unlinked(node:test,lane:foo)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_escaped(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3')
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3")'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_body_int(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3', body=Num.create_from(-100))
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3")-100'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_body_float(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3', body=Num.create_from(-100.0))
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3")-100.0'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_body_bool(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3', body=Bool.create_from(False))
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3")false'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_body_string(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3', body=Text.create_from('spam and \\ham/'))
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3")"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_prio(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3', prio=33.2, body=Text.create_from('spam and \\ham/'))
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3",prio:33.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_rate(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3', rate=0.2, body=Text.create_from('spam and \\ham/'))
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3",rate:0.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_unlinked_prio_rate(self):
        # Given
        envelope = _UnlinkedResponse('/unit/5', '/unit/3', prio=22.11, rate=0.2,
                                     body=Text.create_from('spam and \\ham/'))
        expected = '@unlinked(node:"/unit/5",lane:"/unit/3",prio:22.11,rate:0.2)"spam and \\ham/"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_command(self):
        # Given
        envelope = _CommandMessage('test', 'foo')
        expected = '@command(node:test,lane:foo)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_command_escaped(self):
        # Given
        envelope = _CommandMessage('dead/parrot', 'spam/ham')
        expected = '@command(node:"dead/parrot",lane:"spam/ham")'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_command_body_int(self):
        # Given
        envelope = _CommandMessage('dead/parrot', 'spam/ham', body=Num.create_from(911))
        expected = '@command(node:"dead/parrot",lane:"spam/ham")911'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_command_body_float(self):
        # Given
        envelope = _CommandMessage('dead/parrot', 'spam/ham', body=Num.create_from(-911.119))
        expected = '@command(node:"dead/parrot",lane:"spam/ham")-911.119'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_command_body_bool(self):
        # Given
        envelope = _CommandMessage('dead/parrot', 'spam/ham', body=Bool.create_from(True))
        expected = '@command(node:"dead/parrot",lane:"spam/ham")true'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_command_body_string(self):
        # Given
        envelope = _CommandMessage('dead/parrot', 'spam/ham', body=Text.create_from('Polly the parrot.'))
        expected = '@command(node:"dead/parrot",lane:"spam/ham")"Polly the parrot."'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_command_body_remove(self):
        # Given
        envelope = _CommandMessage('/unit/foo', 'shoppingCart',
                                   body=RecordMap.create_record_map(
                                       Attr.create_attr(Text.create_from('remove'),
                                                        RecordMap.create_record_map(
                                                            Slot.create_slot(Text.create_from('key'),
                                                                             Text.create_from('FromClientLink'))))))
        expected = '@command(node:"/unit/foo",lane:shoppingCart)@remove(key:FromClientLink)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event(self):
        # Given
        envelope = _EventMessage('test', 'foo')
        expected = '@event(node:test,lane:foo)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event_escaped(self):
        # Given
        envelope = _EventMessage('/this/is/spam', 'hello')
        expected = '@event(node:"/this/is/spam",lane:hello)'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event_body_int(self):
        # Given
        envelope = _EventMessage('/this/is/spam', 'hello', body=Num.create_from(1224))
        expected = '@event(node:"/this/is/spam",lane:hello)1224'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event_body_float(self):
        # Given
        envelope = _EventMessage('/this/is/spam', 'hello', body=Num.create_from(33.12))
        expected = '@event(node:"/this/is/spam",lane:hello)33.12'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event_body_bool(self):
        # Given
        envelope = _EventMessage('/this/is/spam', 'hello', body=Bool.create_from(False))
        expected = '@event(node:"/this/is/spam",lane:hello)false'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event_body_string(self):
        # Given
        envelope = _EventMessage('/this/is/spam', 'hello', body=Text.create_from("-33.12 / 6"))
        expected = '@event(node:"/this/is/spam",lane:hello)"-33.12 / 6"'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event_body_object(self):
        # Given
        body = RecordMap.create()
        body.add(Attr.create_attr(Text.create_from('Person'), _Extant._get_extant()))
        body.add(Slot.create_slot(Text.create_from('name'), Text.create_from('Bar')))
        body.add(Slot.create_slot(Text.create_from('age'), Num.create_from(14)))
        body.add(Slot.create_slot(Text.create_from('salary'), Num.create_from(-5.9)))

        envelope = _EventMessage('/this/is/spam', 'hello', body=body)
        expected = '@event(node:"/this/is/spam",lane:hello)@Person{name:Bar,age:14,salary:-5.9}'

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)

    def test_write_event_body_nested(self):
        # Given

        friend = RecordMap.create()
        friend.add(Attr.create_attr(Text.create_from('Person'), _Extant._get_extant()))
        friend.add(Slot.create_slot(Text.create_from('name'), Text.create_from('Sam/Spam')))
        friend.add(Slot.create_slot(Text.create_from('age'), Num.create_from(1)))
        friend.add(Slot.create_slot(Text.create_from('salary'), Num.create_from(22)))

        body = RecordMap.create()
        body.add(Attr.create_attr(Text.create_from('Person'), _Extant._get_extant()))
        body.add(Slot.create_slot(Text.create_from('name'), Text.create_from('Par')))
        body.add(Slot.create_slot(Text.create_from('age'), Num.create_from(11)))
        body.add(Slot.create_slot(Text.create_from('salary'), Num.create_from(-5.9)))
        body.add(Slot.create_slot(Text.create_from('friend'), friend))

        envelope = _EventMessage('/this/is/spam', 'hello', body=body)
        person = '@Person{name:Par,age:11,salary:-5.9,friend:@Person{name:"Sam/Spam",age:1,salary:22}}'
        expected = '@event(node:"/this/is/spam",lane:hello)' + person

        # When
        actual = envelope._to_recon()

        # Then
        self.assertEqual(expected, actual)
