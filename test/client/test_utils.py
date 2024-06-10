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
from urllib.parse import urlparse

from swimos.client._utils import _URI


class TestUtils(unittest.TestCase):

    def test_normalise_scheme_valid_ws(self):
        # Given
        uri = 'ws://foo_bar:9000'
        uri = urlparse(uri)
        # When
        actual = _URI._normalise_scheme(uri)
        # Then
        self.assertEqual('ws', actual)

    def test_normalise_scheme_valid_warp(self):
        # Given
        uri = 'warp://foo_bar:9000'
        uri = urlparse(uri)
        # When
        actual = _URI._normalise_scheme(uri)
        # Then
        self.assertEqual('ws', actual)

    def test_normalise_scheme_valid_wss(self):
        # Given
        uri = 'wss://foo_bar:9000'
        uri = urlparse(uri)
        # When
        actual = _URI._normalise_scheme(uri)
        # Then
        self.assertEqual('wss', actual)

    def test_normalise_scheme_valid_warps(self):
        # Given
        uri = 'warps://foo_bar:9000'
        uri = urlparse(uri)
        # When
        actual = _URI._normalise_scheme(uri)
        # Then
        self.assertEqual('wss', actual)

    def test_normalise_scheme_invalid_empty(self):
        # Given
        uri = 'foo_bar:9000'
        uri = urlparse(uri)
        # When
        actual = _URI._normalise_scheme(uri)
        # Then
        self.assertIsNone(actual)

    def test_normalise_scheme_invalid_http(self):
        # Given
        uri = 'http://foo_bar:9000'
        uri = urlparse(uri)
        # When
        actual = _URI._normalise_scheme(uri)
        # Then
        self.assertIsNone(actual)

    def test_parse_ws_uri(self):
        # Given
        uri = 'ws://foo_bar:9000'
        expected = ('ws://foo_bar:9000', 'ws')
        # When
        actual = _URI._parse_uri(uri)
        # Then
        self.assertEqual(expected, actual)

    def test_parse_warp_uri(self):
        # Given
        uri = 'warp://foo_bar:9000'
        expected = ('ws://foo_bar:9000', 'ws')
        # When
        actual = _URI._parse_uri(uri)
        # Then
        self.assertEqual(expected, actual)

    def test_parse_wss_uri(self):
        # Given
        uri = 'wss://foo_bar:9000'
        expected = ('wss://foo_bar:9000', 'wss')
        # When
        actual = _URI._parse_uri(uri)
        # Then
        self.assertEqual(expected, actual)

    def test_parse_warps_uri(self):
        # Given
        uri = 'warps://foo_bar:9000'
        expected = ('wss://foo_bar:9000', 'wss')
        # When
        actual = _URI._parse_uri(uri)
        # Then
        self.assertEqual(expected, actual)

    def test_parse_invalid_scheme_uri(self):
        # Given
        uri = 'carp://foo_bar:9000'
        # When
        with self.assertRaises(TypeError) as error:
            _URI._parse_uri(uri)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Invalid scheme "carp" for Warp URI!', message)
