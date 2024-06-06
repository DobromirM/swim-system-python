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

from swimos.structures import RecordMap, Attr, Text, Slot
from swimos.recon import Recon
from swimos.recon._parsers import _ReconParser
from swimos.recon._writers import _ReconWriter


class TestRecon(unittest.TestCase):

    def test_parse(self):
        # Given
        recon_string = '@sync(node: "foo/node", lane: "foo/lane")"Hello, World"'
        # When
        actual = Recon.parse(recon_string)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual('sync', actual._tag)
        self.assertEqual(2, actual.size)
        self.assertEqual('foo/node', actual.get_item(0).value.get_item(0).value.value)
        self.assertEqual('foo/lane', actual.get_item(0).value.get_item(1).value.value)
        self.assertEqual('Hello, World', actual.get_item(1).value)

    def test_to_string(self):
        # Given
        value = RecordMap.create()
        value.add(Attr.create_attr(Text.create_from('remove'),
                                   RecordMap.create_record_map(
                                       Slot.create_slot(Text.create_from('key'), Text.create_from('foo')))))
        # When
        actual = Recon.to_string(value)
        # Then
        self.assertEqual('@remove(key:foo)', actual)

    def test_get_writer_once(self):
        # When
        actual = Recon._get_writer()
        # Then
        self.assertIsInstance(actual, _ReconWriter)
        self.assertEqual(Recon._get_writer(), actual)

    def test_get_writer_multiple(self):
        # Given
        expected = Recon._get_writer()
        # When
        actual = Recon._get_writer()
        # Then
        self.assertIsInstance(actual, _ReconWriter)
        self.assertEqual(expected, actual)
        self.assertEqual(Recon._get_writer(), actual)

    def get_parser_once(self):
        # When
        actual = Recon._get_parser()
        # Then
        self.assertIsInstance(actual, _ReconParser)
        self.assertEqual(Recon._get_parser(), actual)

    def get_parser_multiple(self):
        # Given
        expected = Recon._get_parser()
        # When
        actual = Recon._get_parser()
        # Then
        self.assertIsInstance(actual, _ReconParser)
        self.assertEqual(expected, actual)
        self.assertEqual(Recon._get_parser(), actual)
