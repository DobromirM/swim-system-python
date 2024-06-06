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

from swimos.recon._parsers import _ReconUtils, _OutputMessage, _InputMessage
from test.utils import CustomString


class TestUtils(unittest.TestCase):

    def test_is_valid_ident_start_char_A(self):
        # Given
        character = 'A'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_start_char_Z(self):
        # Given
        character = 'Z'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_start_char_P(self):
        # Given
        character = 'P'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_start_char_a(self):
        # Given
        character = 'a'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_start_char_z(self):
        # Given
        character = 'z'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_start_char_h(self):
        # Given
        character = 'h'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_start_char_underscore(self):
        # Given
        character = '_'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_invalid_ident_start_char_digit(self):
        # Given
        character = '4'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_start_char_hyphen(self):
        # Given
        character = '-'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_start_char_dollar(self):
        # Given
        character = '$'
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_start_char_empty(self):
        # Given
        character = ''
        # When
        actual = _ReconUtils._is_ident_start_char(character)
        # Then
        self.assertFalse(actual)

    def test_is_valid_ident_char_A(self):
        # Given
        character = 'A'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_Z(self):
        # Given
        character = 'Z'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_N(self):
        # Given
        character = 'N'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_a(self):
        # Given
        character = 'a'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_z(self):
        # Given
        character = 'z'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_g(self):
        # Given
        character = 'g'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_underscore(self):
        # Given
        character = '_'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_hyphen(self):
        # Given
        character = '-'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_0(self):
        # Given
        character = '0'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_9(self):
        # Given
        character = '9'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_ident_char_5(self):
        # Given
        character = '5'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertTrue(actual)

    def test_is_invalid_ident_char_dollar(self):
        # Given
        character = '$'
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_char_empty(self):
        # Given
        character = ''
        # When
        actual = _ReconUtils._is_ident_char(character)
        # Then
        self.assertFalse(actual)

    def test_is_valid_ident(self):
        # Given
        value = 'test1'
        # When
        actual = _ReconUtils._is_ident(value)
        # Then
        self.assertTrue(actual)

    def test_is_invalid_ident_empty(self):
        # Given
        value = ''
        # When
        actual = _ReconUtils._is_ident(value)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_invalid_start_char(self):
        # Given
        value = '1test'
        # When
        actual = _ReconUtils._is_ident(value)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_invalid_middle_char(self):
        # Given
        value = 'test$test'
        # When
        actual = _ReconUtils._is_ident(value)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_invalid_end_char(self):
        # Given
        value = 'test$'
        # When
        actual = _ReconUtils._is_ident(value)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_ident_invalid_all_chars(self):
        # Given
        value = '^%&*'
        # When
        actual = _ReconUtils._is_ident(value)
        # Then
        self.assertFalse(actual)

    def test_is_valid_space_char_space(self):
        # Given
        character = ' '
        # When
        actual = _ReconUtils._is_space(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_space_char_tab(self):
        # Given
        character = '\t'
        # When
        actual = _ReconUtils._is_space(character)
        # Then
        self.assertTrue(actual)

    def test_is_invalid_space_char_digit(self):
        # Given
        character = '5'
        # When
        actual = _ReconUtils._is_space(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_space_char_letter(self):
        # Given
        character = 'l'
        # When
        actual = _ReconUtils._is_space(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_space_char_empty(self):
        # Given
        character = ''
        # When
        actual = _ReconUtils._is_space(character)
        # Then
        self.assertFalse(actual)

    def test_is_valid_digit_char_1(self):
        # Given
        character = '2'
        # When
        actual = _ReconUtils._is_digit(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_digit_char_0(self):
        # Given
        character = '0'
        # When
        actual = _ReconUtils._is_digit(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_digit_char_7(self):
        # Given
        character = '7'
        # When
        actual = _ReconUtils._is_digit(character)
        # Then
        self.assertTrue(actual)

    def test_is_valid_digit_char_9(self):
        # Given
        character = '9'
        # When
        actual = _ReconUtils._is_digit(character)
        # Then
        self.assertTrue(actual)

    def test_is_invalid_digit_char_letter(self):
        # Given
        character = 'b'
        # When
        actual = _ReconUtils._is_digit(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_digit_char_underscore(self):
        # Given
        character = '_'
        # When
        actual = _ReconUtils._is_digit(character)
        # Then
        self.assertFalse(actual)

    def test_is_invalid_digit_char_empty(self):
        # Given
        character = ''
        # When
        actual = _ReconUtils._is_digit(character)
        # Then
        self.assertFalse(actual)

    def test_to_ord_str(self):
        # Given
        character = 'p'
        # When
        actual = _ReconUtils._to_ord(character)
        # Then
        self.assertEqual(112, actual)

    def test_to_ord_int(self):
        # Given
        character = 3
        # When
        actual = _ReconUtils._to_ord(character)
        # Then
        self.assertEqual(3, actual)

    def test_to_ord_other(self):
        # Given
        character = 3.12
        # When
        actual = _ReconUtils._to_ord(character)
        # Then
        self.assertEqual(None, actual)

    def test_output_message_create_empty(self):
        # Given
        chars = None
        # When
        actual = _OutputMessage._create(chars)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('', actual._value)
        self.assertEqual(0, actual._size)
        self.assertEqual('', actual._last_char)

    def test_output_message_create_single(self):
        # Given
        chars = 'p'
        # When
        actual = _OutputMessage._create(chars)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('p', actual._value)
        self.assertEqual(1, actual._size)
        self.assertEqual('p', actual._last_char)

    def test_output_message_create_multiple(self):
        # Given
        chars = 'foo_bar'
        # When
        actual = _OutputMessage._create(chars)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('foo_bar', actual._value)
        self.assertEqual(7, actual._size)
        self.assertEqual('r', actual._last_char)

    def test_output_message_append_str_to_empty(self):
        # Given
        output_message = _OutputMessage._create('')
        chars = 'bar'
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('bar', output_message._value)
        self.assertEqual(3, output_message._size)
        self.assertEqual('r', output_message._last_char)

    def test_output_message_append_float_to_empty(self):
        # Given
        output_message = _OutputMessage._create('')
        chars = 21.12
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('21.12', output_message._value)
        self.assertEqual(5, output_message._size)
        self.assertEqual('2', output_message._last_char)

    def test_output_message_append_int_to_empty(self):
        # Given
        output_message = _OutputMessage._create('')
        chars = 13
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('13', output_message._value)
        self.assertEqual(2, output_message._size)
        self.assertEqual('3', output_message._last_char)

    def test_output_message_append_output_message_to_empty(self):
        # Given
        output_message = _OutputMessage._create('')
        chars = _OutputMessage._create('boo_fast')
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('boo_fast', output_message._value)
        self.assertEqual(8, output_message._size)
        self.assertEqual('t', output_message._last_char)

    def test_output_message_append_input_message_to_empty(self):
        # Given
        output_message = _OutputMessage._create('')
        chars = _InputMessage._create('my_message')
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('my_message', output_message._value)
        self.assertEqual(10, output_message._size)
        self.assertEqual('e', output_message._last_char)

    def test_output_message_append_invalid_to_empty(self):
        # Given
        output_message = _OutputMessage._create('')
        chars = CustomString('moo')
        # When
        with self.assertRaises(TypeError) as error:
            output_message._append(chars)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Item of type CustomString cannot be added to Message!', message)

    def test_output_message_append_str_to_existing(self):
        # Given
        output_message = _OutputMessage._create('full')
        chars = '_qux'
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('full_qux', output_message._value)
        self.assertEqual(8, output_message._size)
        self.assertEqual('x', output_message._last_char)

    def test_output_message_append_float_to_existing(self):
        # Given
        output_message = _OutputMessage._create('full')
        chars = 22.1
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('full22.1', output_message._value)
        self.assertEqual(8, output_message._size)
        self.assertEqual('1', output_message._last_char)

    def test_output_message_append_int_to_existing(self):
        # Given
        output_message = _OutputMessage._create('empty')
        chars = 73
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('empty73', output_message._value)
        self.assertEqual(7, output_message._size)
        self.assertEqual('3', output_message._last_char)

    def test_output_message_append_output_message_to_existing(self):
        # Given
        output_message = _OutputMessage._create('empty')
        chars = _OutputMessage._create(' house')
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('empty house', output_message._value)
        self.assertEqual(11, output_message._size)
        self.assertEqual('e', output_message._last_char)

    def test_output_message_append_input_message_to_existing(self):
        # Given
        output_message = _OutputMessage._create('input_')
        chars = _InputMessage._create('message')
        # When
        output_message._append(chars)
        # Then
        self.assertIsInstance(output_message, _OutputMessage)
        self.assertEqual('input_message', output_message._value)
        self.assertEqual(13, output_message._size)
        self.assertEqual('e', output_message._last_char)

    def test_output_message_append_invalid_to_existing(self):
        # Given
        output_message = _OutputMessage._create('bar')
        chars = CustomString('foo')
        # When
        with self.assertRaises(TypeError) as error:
            output_message._append(chars)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Item of type CustomString cannot be added to Message!', message)

    def test_input_message_create_empty(self):
        # Given
        chars = None
        # When
        actual = _InputMessage._create(chars)
        # Then
        self.assertIsInstance(actual, _InputMessage)
        self.assertEqual('', actual._value)
        self.assertEqual(0, actual._size)
        self.assertEqual('', actual._head)
        self.assertFalse(actual._is_cont)

    def test_input_message_create_single(self):
        # Given
        chars = 'm'
        # When
        actual = _InputMessage._create(chars)
        # Then
        self.assertIsInstance(actual, _InputMessage)
        self.assertEqual('m', actual._value)
        self.assertEqual(1, actual._size)
        self.assertEqual('m', actual._head)
        self.assertTrue(actual._is_cont)

    def test_input_message_create_multiple(self):
        # Given
        chars = 'moo_cow'
        # When
        actual = _InputMessage._create(chars)
        # Then
        self.assertIsInstance(actual, _InputMessage)
        self.assertEqual('moo_cow', actual._value)
        self.assertEqual(7, actual._size)
        self.assertEqual('m', actual._head)
        self.assertTrue(actual._is_cont)

    def test_input_message_append_str_to_empty(self):
        # Given
        input_message = _InputMessage._create('')
        chars = 'test'
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('test', input_message._value)
        self.assertEqual(4, input_message._size)
        self.assertEqual('t', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_float_to_empty(self):
        # Given
        input_message = _InputMessage._create('')
        chars = -0.12
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('-0.12', input_message._value)
        self.assertEqual(5, input_message._size)
        self.assertEqual('-', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_int_to_empty(self):
        # Given
        input_message = _InputMessage._create('')
        chars = -32
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('-32', input_message._value)
        self.assertEqual(3, input_message._size)
        self.assertEqual('-', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_input_message_to_empty(self):
        # Given
        input_message = _InputMessage._create('')
        chars = _InputMessage._create('input_bar')
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('input_bar', input_message._value)
        self.assertEqual(9, input_message._size)
        self.assertEqual('i', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_output_message_to_empty(self):
        # Given
        input_message = _InputMessage._create('')
        chars = _OutputMessage._create('output_bar')
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('output_bar', input_message._value)
        self.assertEqual(10, input_message._size)
        self.assertEqual('o', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_invalid_to_empty(self):
        # Given
        input_message = _InputMessage._create('')
        chars = None
        # When
        with self.assertRaises(TypeError) as error:
            input_message._append(chars)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Item of type NoneType cannot be added to Message!', message)

    def test_input_message_append_str_to_existing(self):
        # Given
        input_message = _InputMessage._create('cow')
        chars = '_moo'
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('cow_moo', input_message._value)
        self.assertEqual(7, input_message._size)
        self.assertEqual('c', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_float_to_existing(self):
        # Given
        input_message = _InputMessage._create('paw_')
        chars = -1.23
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('paw_-1.23', input_message._value)
        self.assertEqual(9, input_message._size)
        self.assertEqual('p', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_int_to_existing(self):
        # Given
        input_message = _InputMessage._create('+-111')
        chars = -1112
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('+-111-1112', input_message._value)
        self.assertEqual(10, input_message._size)
        self.assertEqual('+', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_input_message_to_existing(self):
        # Given
        input_message = _InputMessage._create('+_/2')
        chars = _InputMessage._create('10-1-2')
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('+_/210-1-2', input_message._value)
        self.assertEqual(10, input_message._size)
        self.assertEqual('+', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_output_message_to_existing(self):
        # Given
        input_message = _InputMessage._create('bar')
        chars = _OutputMessage._create('_foo')
        # When
        input_message._append(chars)
        # Then
        self.assertIsInstance(input_message, _InputMessage)
        self.assertEqual('bar_foo', input_message._value)
        self.assertEqual(7, input_message._size)
        self.assertEqual('b', input_message._head)
        self.assertTrue(input_message._is_cont)

    def test_input_message_append_invalid_to_existing(self):
        # Given
        input_message = _InputMessage._create('bar')
        chars = None
        # When
        with self.assertRaises(TypeError) as error:
            input_message._append(chars)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Item of type NoneType cannot be added to Message!', message)

    def test_input_message_skip_spaces_none(self):
        # Given
        message = _InputMessage._create('foo')
        # When
        message._skip_spaces(message)
        # Then
        self.assertEqual('f', message._head)

    def test_input_message_skip_spaces_single(self):
        # Given
        message = _InputMessage._create(' bar')
        # When
        message._skip_spaces(message)
        # Then
        self.assertEqual('b', message._head)

    def test_input_message_skip_spaces_multiple(self):
        # Given
        message = _InputMessage._create('    qux')
        # When
        message._skip_spaces(message)
        # Then
        self.assertEqual('q', message._head)

    def test_input_message_skip_spaces_spaces_only(self):
        # Given
        message = _InputMessage._create('    ')
        # When
        message._skip_spaces(message)
        # Then
        self.assertEqual('', message._head)

    def test_input_message_head_empty(self):
        # Given
        message = _InputMessage._create('')
        # When
        actual = message._head
        # Then
        self.assertEqual('', actual)

    def test_input_message_head_continuous(self):
        # Given
        message = _InputMessage._create('abc')
        # When
        message._step()
        actual = message._head
        # Then
        self.assertEqual('b', actual)

    def test_input_message_head_not_continuous(self):
        # Given
        message = _InputMessage._create('abc')
        # When
        message._step()
        message._step()
        message._step()
        actual = message._head
        # Then
        self.assertEqual('', actual)

    def test_input_message_is_continuous_empty(self):
        # Given
        message = _InputMessage._create('')
        # When
        actual = message._is_cont
        # Then
        self.assertFalse(actual)

    def test_input_message_is_continuous_existing_true(self):
        # Given
        message = _InputMessage._create('dog')
        # When
        actual = message._is_cont
        # Then
        self.assertTrue(actual)

    def test_input_message_is_continuous_existing_false(self):
        # Given
        message = _InputMessage._create('dog')
        # When
        message._step()
        message._step()
        message._step()
        actual = message._is_cont
        # Then
        self.assertFalse(actual)

    def test_input_message_step_once(self):
        # Given
        message = _InputMessage._create('dog')
        # When
        actual = message._step()
        # Then
        self.assertEqual('o', actual)

    def test_input_message_step_twice(self):
        # Given
        message = _InputMessage._create('dog')
        # When
        message._step()
        actual = message._step()
        # Then
        self.assertEqual('g', actual)

    def test_input_message_step_out_of_bound(self):
        # Given
        message = _InputMessage._create('dog')
        # When
        message._step()
        message._step()
        message._step()
        actual = message._step()
        # Then
        self.assertEqual('', actual)
