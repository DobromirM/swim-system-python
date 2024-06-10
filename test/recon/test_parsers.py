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

from swimos.recon._parsers import _ReconParser, _InputMessage, _OutputMessage, _DecimalParser
from swimos.structures import RecordMap, Slot, Text, Attr, Num, Bool
from swimos.structures._structs import _Absent


class TestParsers(unittest.TestCase):

    def test_parse_literal_slot_empty_builder(self):
        # Given
        message = _InputMessage._create('{foo: bar}')
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertIsInstance(actual, RecordMap)
        self.assertIsInstance(actual.get_item(0), Slot)
        self.assertIsInstance(actual.get_item(0).key, Text)
        self.assertEqual('foo', actual.get_item(0).key.value)
        self.assertIsInstance(actual.get_item(0).value, Text)
        self.assertEqual('bar', actual.get_item(0).value.value)

    def test_parse_literal_slot_existing_builder(self):
        # Given
        message = _InputMessage._create('{Foo: Bar}')
        builder = _ReconParser._create_value_builder()
        builder.add(Attr.create_attr('Baz', 'Qux'))
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message, builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertIsInstance(actual.get_item(0), Attr)
        self.assertIsInstance(actual.get_item(0).key, Text)
        self.assertEqual('Baz', actual.get_item(0).key.value)
        self.assertIsInstance(actual.get_item(0).value, str)
        self.assertEqual('Qux', actual.get_item(0).value)
        self.assertIsInstance(actual.get_item(1), Slot)
        self.assertIsInstance(actual.get_item(1).key, Text)
        self.assertEqual('Foo', actual.get_item(1).key.value)
        self.assertIsInstance(actual.get_item(1).value, Text)
        self.assertEqual('Bar', actual.get_item(1).value.value)

    def test_parse_literal_ident_empty_builder(self):
        # Given
        message = _InputMessage._create('foo')
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('foo', actual.value)
        self.assertEqual(_Absent._get_absent(), actual.key)

    def test_parse_literal_ident_existing_builder(self):
        # Given
        message = _InputMessage._create('foo')
        builder = _ReconParser._create_value_builder()
        builder.add(Text.create_from('bar'))
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message, builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertIsInstance(actual.get_item(0), Text)
        self.assertIsInstance(actual.get_item(1), Text)
        self.assertEqual('bar', actual.get_item(0).value)
        self.assertEqual('foo', actual.get_item(1).value)

    def test_parse_literal_quote_empty_builder(self):
        # Given
        message = _InputMessage._create('"Baz_Foo"')
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertIsInstance(actual.value, str)
        self.assertEqual('Baz_Foo', actual.value)

    def test_parse_literal_quote_existing_builder(self):
        # Given
        message = _InputMessage._create('"Hello_World"')
        builder = _ReconParser._create_value_builder()
        parser = _ReconParser()
        builder.add(Text.create_from('Hi'))
        builder.add(Text.create_from('Bye'))
        # When
        actual = parser._parse_literal(message, builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(3, actual.size)
        self.assertIsInstance(actual.get_item(0), Text)
        self.assertIsInstance(actual.get_item(1), Text)
        self.assertIsInstance(actual.get_item(2), Text)
        self.assertEqual('Hi', actual.get_item(0).value)
        self.assertEqual('Bye', actual.get_item(1).value)
        self.assertEqual('Hello_World', actual.get_item(2).value)

    def test_parse_literal_minus_empty_builder(self):
        # Given
        message = _InputMessage._create('-13.42')
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertIsInstance(actual.value, float)
        self.assertEqual(-13.42, actual.value)

    def test_parse_literal_minus_existing_builder(self):
        # Given
        message = _InputMessage._create('  37')
        parser = _ReconParser()
        builder = _ReconParser._create_value_builder()
        builder.add(Text.create_from('Hello'))
        builder.add(Text.create_from('Friend'))
        # When
        actual = parser._parse_literal(message, builder)
        # Then
        self.assertEqual(3, actual.size)
        self.assertIsInstance(actual, RecordMap)
        self.assertIsInstance(actual.get_item(0), Text)
        self.assertIsInstance(actual.get_item(1), Text)
        self.assertIsInstance(actual.get_item(2), Num)
        self.assertEqual('Hello', actual.get_item(0).value)
        self.assertEqual('Friend', actual.get_item(1).value)
        self.assertEqual(37, actual.get_item(2).value)

    def test_parse_literal_empty_empty_builder(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message)
        # Then
        self.assertEqual(_Absent._get_absent(), actual)

    def test_parse_literal_empty_existing_builder(self):
        # Given
        message = _InputMessage._create('')
        builder = _ReconParser._create_value_builder()
        builder.add(Text.create_from('Hello'))
        parser = _ReconParser()
        # When
        actual = parser._parse_literal(message, builder)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual(0, actual.size)
        self.assertEqual('Hello', actual.value)

    def test_parse_decimal_positive_empty_value(self):
        # Given
        message = _InputMessage._create('.32')
        parser = _ReconParser()
        # When
        actual = _DecimalParser._parse(message, parser)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.32, actual.value)

    def test_parse_decimal_positive_existing_value(self):
        # Given
        message = _InputMessage._create('.691')
        parser = _ReconParser()
        value_output = 12
        # When
        actual = _DecimalParser._parse(message, parser, value_output)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(12.691, actual.value)

    def test_parse_decimal_negative_empty_value(self):
        # Given
        message = _InputMessage._create('.1')
        parser = _ReconParser()
        # When
        actual = _DecimalParser._parse(message, parser, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.1, actual.value)

    def test_parse_decimal_negative_existing_value(self):
        # Given
        message = _InputMessage._create('.1091')
        parser = _ReconParser()
        value_output = -13
        # When
        actual = _DecimalParser._parse(message, parser, value_output, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-13.1091, actual.value)

    def test_parse_decimal_empty_positive_empty_value(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        # When
        actual = _DecimalParser._parse(message, parser)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.0, actual.value)

    def test_parse_decimal_empty_positive_existing_value(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        value_output = 15
        # When
        actual = _DecimalParser._parse(message, parser, value_output)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(15.0, actual.value)

    def test_parse_decimal_empty_negative_empty_value(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        # When
        actual = _DecimalParser._parse(message, parser, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.0, actual.value)

    def test_parse_decimal_empty_negative_existing_value(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        value_output = -16
        # When
        actual = _DecimalParser._parse(message, parser, value_output, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-16.0, actual.value)

    def test_parse_decimal_dot_only_positive_empty_value(self):
        # Given
        message = _InputMessage._create('.')
        parser = _ReconParser()
        # When
        actual = _DecimalParser._parse(message, parser)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.0, actual.value)

    def test_parse_decimal_dot_only_positive_existing_value(self):
        # Given
        message = _InputMessage._create('.')
        parser = _ReconParser()
        value_output = 17
        # When
        actual = _DecimalParser._parse(message, parser, value_output)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(17.0, actual.value)

    def test_parse_decimal_dot_only_negative_empty_value(self):
        # Given
        message = _InputMessage._create('.')
        parser = _ReconParser()
        # When
        actual = _DecimalParser._parse(message, parser, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.0, actual.value)

    def test_parse_decimal_dot_only_negative_existing_value(self):
        # Given
        message = _InputMessage._create('.')
        parser = _ReconParser()
        value_output = -18
        # When
        actual = _DecimalParser._parse(message, parser, value_output, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-18.0, actual.value)

    def test_parse_number_positive_int(self):
        # Given
        message = _InputMessage._create(' 112')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(112, actual.value)

    def test_parse_number_negative_int(self):
        # Given
        message = _InputMessage._create('-90')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-90, actual.value)

    def test_parse_number_positive_float_full(self):
        # Given
        message = _InputMessage._create('91.11')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(91.11, actual.value)

    def test_parse_number_negative_float_full(self):
        # Given
        message = _InputMessage._create('  -11.12')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-11.12, actual.value)

    def test_parse_number_positive_float_decimal_only(self):
        # Given
        message = _InputMessage._create('  .12')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.12, actual.value)

    def test_parse_number_negative_float_decimal_only(self):
        # Given
        message = _InputMessage._create('  .31')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.31, actual.value)

    def test_parse_number_float_point_only(self):
        # Given
        message = _InputMessage._create('.')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.00, actual.value)

    def test_parse_number_empty(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0, actual.value)

    def test_parse_number_leading_zero(self):
        # Given
        message = _InputMessage._create('012')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(12, actual.value)

    def test_parse_number_leading_zeroes(self):
        # Given
        message = _InputMessage._create('00013')
        parser = _ReconParser()
        # When
        actual = parser._parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(13, actual.value)

    def test_parse_string_normal(self):
        # Given
        message = _InputMessage._create('"Hello, friend"')
        parser = _ReconParser()
        # When
        actual = parser._parse_string(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('Hello, friend', actual.value)

    def test_parse_string_missing_closing_quote(self):
        # Given
        message = _InputMessage._create('  "Hello, World')
        parser = _ReconParser()
        # When
        actual = parser._parse_string(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('Hello, World', actual.value)

    def test_parse_string_existing_output(self):
        # Given
        message = _InputMessage._create('"dog"')
        output = _OutputMessage._create('This is ')
        parser = _ReconParser()
        # When
        actual = parser._parse_string(message, output)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('This is dog', actual.value)

    def test_parse_string_empty(self):
        # Given
        message = _InputMessage()
        parser = _ReconParser()
        # When
        actual = parser._parse_string(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('', actual.value)

    def test_parse_ident_valid(self):
        # Given
        message = _InputMessage._create('test')
        parser = _ReconParser()
        # When
        actual = parser._parse_ident(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('test', actual.value)

    def test_parse_ident_valid_with_leading_spaces(self):
        # Given
        message = _InputMessage._create('   foo')
        parser = _ReconParser()
        # When
        actual = parser._parse_ident(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('foo', actual.value)

    def test_parse_ident_valid_with_output(self):
        # Given
        message = _InputMessage._create('   foo')
        parser = _ReconParser()
        output = _OutputMessage._create('bar_')
        # When
        actual = parser._parse_ident(message, output)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('bar_foo', actual.value)

    def test_parse_ident_invalid_with_output(self):
        # Given
        message = _InputMessage._create('$$')
        parser = _ReconParser()
        output = _OutputMessage._create('hello')
        # When
        actual = parser._parse_ident(message, output)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('hello', actual.value)

    def test_parse_ident_invalid(self):
        # Given
        message = _InputMessage._create('$lane: test')
        parser = _ReconParser()
        # When
        with self.assertRaises(TypeError) as error:
            parser._parse_ident(message)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Identifier starting at position 0 is invalid!\nMessage: $lane: test', message)

    def test_parse_ident_empty(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        # When
        with self.assertRaises(TypeError) as error:
            parser._parse_ident(message)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Identifier starting at position 0 is invalid!\nMessage: ', message)

    def test_parse_attr_no_body(self):
        # Given
        message = _InputMessage._create('@animal')
        parser = _ReconParser()
        # When
        actual = parser._parse_attr(message)
        # Then
        self.assertIsInstance(actual, Attr)
        self.assertIsInstance(actual.key, Text)
        self.assertEqual('animal', actual.key.value)

    def test_parse_attr_slot_key_only(self):
        # Given
        message = _InputMessage._create('@animal(node)')
        parser = _ReconParser()
        # When
        actual = parser._parse_attr(message)
        # Then
        self.assertIsInstance(actual, Attr)
        self.assertIsInstance(actual.key, Text)
        self.assertEqual('animal', actual.key.value)
        self.assertIsInstance(actual.value, RecordMap)
        self.assertEqual(1, actual.value.size)
        self.assertIsInstance(actual.value.get_item(0), Text)
        self.assertEqual('node', actual.value.get_item(0).value)

    def test_parse_attr_slot_key_and_value(self):
        # Given
        message = _InputMessage._create('@vehicle(car: red)')
        parser = _ReconParser()
        # When
        actual = parser._parse_attr(message)
        # Then
        self.assertIsInstance(actual, Attr)
        self.assertIsInstance(actual.key, Text)
        self.assertEqual('vehicle', actual.key.value)
        self.assertEqual(1, actual.value.size)
        self.assertIsInstance(actual.value, RecordMap)
        self.assertIsInstance(actual.value.get_item(0), Slot)
        self.assertEqual('car', actual.value.get_item(0).key.value)
        self.assertEqual('red', actual.value.get_item(0).value.value)

    def test_parse_attr_existing_key_and_value(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        key_output = Text.create_from('Baz')
        value_output = Text.create_from('Qux')
        # When
        actual = parser._parse_attr(message, key_output, value_output)
        # Then
        self.assertIsInstance(actual, Attr)
        self.assertIsInstance(actual.key, Text)
        self.assertIsInstance(actual.value, Text)
        self.assertEqual('Baz', actual.key.value)
        self.assertEqual('Qux', actual.value.value)

    def test_parse_attr_empty(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        # When
        with self.assertRaises(TypeError) as error:
            parser._parse_attr(message)
        # Then
        message = error.exception.args[0]
        self.assertEqual('Attribute starting at position 0 is invalid!\nMessage: ', message)

    def test_attr_expression_parser_parse_attribute(self):
        # Given
        message = _InputMessage._create('@test')
        parser = _ReconParser()
        # When
        actual = parser._parse_attr_expression(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertEqual('test', actual._tag)

    def test_attr_expression_parser_parse_attribute_existing_field(self):
        # Given
        message = _InputMessage._create('@test')
        parser = _ReconParser()
        builder = RecordMap.create()
        builder.add(Text.create_from('Moo'))
        field = Text.create_from('Boo')
        # When
        actual = parser._parse_attr_expression(message, builder=builder, field_output=field)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(3, actual.size)
        self.assertEqual('Moo', actual.get_item(0).value)
        self.assertEqual('Boo', actual.get_item(1).value)
        self.assertEqual('test', actual.get_item(2).key.value)

    def test_attr_expression_parser_parse_literal(self):
        # Given
        message = _InputMessage._create('literal')
        parser = _ReconParser()
        # When
        actual = parser._parse_attr_expression(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('literal', actual.value)

    def test_attr_expression_parser_parse_literal_existing_value(self):
        # Given
        message = _InputMessage._create('literal')
        parser = _ReconParser()
        builder = RecordMap.create()
        builder.add(Text.create_from('Moo'))
        value = Text.create_from('Dog')
        # When
        actual = parser._parse_attr_expression(message, builder=builder, value_output=value)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(3, actual.size)
        self.assertEqual('Moo', actual.get_item(0).value)
        self.assertEqual('Dog', actual.get_item(1).value)
        self.assertEqual('literal', actual.get_item(2).value)

    def test_attr_expression_parser_parse_record_curly_brackets(self):
        # Given
        message = _InputMessage._create('{record}')
        parser = _ReconParser()
        # When
        actual = parser._parse_attr_expression(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertEqual('record', actual.get_item(0).value)

    def test_attr_expression_parser_parse_record_square_brackets(self):
        # Given
        message = _InputMessage._create('[record]')
        parser = _ReconParser()
        # When
        actual = parser._parse_attr_expression(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertEqual('record', actual.get_item(0).value)

    def test_record_parser_parse_single(self):
        # Given
        message = _InputMessage._create('{animal: dog}')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertEqual('animal', actual.get_item(0).key.value)
        self.assertEqual('dog', actual.get_item(0).value.value)

    def test_record_parser_parse_double(self):
        # Given
        message = _InputMessage._create('{cat: meow, dog: bark}')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('cat', actual.get_item(0).key.value)
        self.assertEqual('meow', actual.get_item(0).value.value)
        self.assertEqual('dog', actual.get_item(1).key.value)
        self.assertEqual('bark', actual.get_item(1).value.value)

    def test_record_parser_parse_multiple(self):
        # Given
        message = _InputMessage._create('{dog: bark,  bird: chirp , cat  : meow }')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(3, actual.size)
        self.assertEqual('dog', actual.get_item(0).key.value)
        self.assertEqual('bark', actual.get_item(0).value.value)
        self.assertEqual('bird', actual.get_item(1).key.value)
        self.assertEqual('chirp', actual.get_item(1).value.value)
        self.assertEqual('cat', actual.get_item(2).key.value)
        self.assertEqual('meow', actual.get_item(2).value.value)

    def test_record_parser_parse_square_brackets(self):
        # Given
        message = _InputMessage._create('[pet: mouse]')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertEqual('pet', actual.get_item(0).key.value)
        self.assertEqual('mouse', actual.get_item(0).value.value)

    def test_record_parser_parse_no_brackets(self):
        # Given
        message = _InputMessage._create('duck: quack, dog: bark')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('duck', actual.get_item(0).key.value)
        self.assertEqual('quack', actual.get_item(0).value.value)
        self.assertEqual('dog', actual.get_item(1).key.value)
        self.assertEqual('bark', actual.get_item(1).value.value)

    def test_record_parser_parse_semicolon_delimiter(self):
        # Given
        message = _InputMessage._create('{large_dog: collie ; small_dog: pug}')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('large_dog', actual.get_item(0).key.value)
        self.assertEqual('collie', actual.get_item(0).value.value)
        self.assertEqual('small_dog', actual.get_item(1).key.value)
        self.assertEqual('pug', actual.get_item(1).value.value)

    def test_record_parser_parse_missing_closing_bracket(self):
        # Given
        message = _InputMessage._create('{hello: world, bye: world')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('hello', actual.get_item(0).key.value)
        self.assertEqual('world', actual.get_item(0).value.value)
        self.assertEqual('bye', actual.get_item(1).key.value)
        self.assertEqual('world', actual.get_item(1).value.value)

    def test_record_parser_parse_missing_opening_bracket(self):
        # Given
        message = _InputMessage._create('bye: world, hello: world}')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('bye', actual.get_item(0).key.value)
        self.assertEqual('world', actual.get_item(0).value.value)
        self.assertEqual('hello', actual.get_item(1).key.value)
        self.assertEqual('world', actual.get_item(1).value.value)

    def test_record_parser_parse_key_only(self):
        # Given
        message = _InputMessage._create('{foo}')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertIsInstance(actual.get_item(0), Text)
        self.assertEqual('foo', actual.get_item(0).value)

    def test_record_parser_parse_existing_key_empty(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        key = Text.create_from('dog')
        # When
        actual = parser._parse_record(message, key_output=key)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertIsInstance(actual.get_item(0), Slot)
        self.assertEqual('dog', actual.get_item(0).key.value)

    def test_record_parser_parse_existing_key_value(self):
        # Given
        message = _InputMessage._create(':dog')
        parser = _ReconParser()
        key = Text.create_from('animal')
        # When
        actual = parser._parse_record(message, key_output=key)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertEqual('animal', actual.get_item(0).key.value)
        self.assertEqual('dog', actual.get_item(0).value.value)

    def test_record_parser_parse_existing_key_multiple(self):
        # Given
        message = _InputMessage._create(':dog, test:bar')
        parser = _ReconParser()
        key = Text.create_from('animal')
        # When
        actual = parser._parse_record(message, key_output=key)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('animal', actual.get_item(0).key.value)
        self.assertEqual('dog', actual.get_item(0).value.value)
        self.assertEqual('test', actual.get_item(1).key.value)
        self.assertEqual('bar', actual.get_item(1).value.value)

    def test_record_parser_parse_existing_value_multiple(self):
        # Given
        message = _InputMessage._create('animal, test:foo')
        parser = _ReconParser()
        value = Text.create_from('cat')
        # When
        actual = parser._parse_record(message, value_output=value)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('animal', actual.get_item(0).key.value)
        self.assertEqual('cat', actual.get_item(0).value.value)
        self.assertEqual('test', actual.get_item(1).key.value)
        self.assertEqual('foo', actual.get_item(1).value.value)

    def test_record_parser_parse_existing_builder_empty(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        builder = parser._create_record_builder()
        builder.add(parser._create_slot(Text.create_from('cow'), Text.create_from('moo')))
        # When
        actual = parser._parse_record(message, builder=builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(1, actual.size)
        self.assertEqual('cow', actual.get_item(0).key.value)
        self.assertEqual('moo', actual.get_item(0).value.value)

    def test_record_parser_parse_existing_builder_single(self):
        # Given
        message = _InputMessage._create(' cat: meow')
        parser = _ReconParser()
        builder = parser._create_record_builder()
        builder.add(parser._create_slot(Text.create_from('dog'), Text.create_from('bark')))
        # When
        actual = parser._parse_record(message, builder=builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertEqual('dog', actual.get_item(0).key.value)
        self.assertEqual('bark', actual.get_item(0).value.value)
        self.assertEqual('cat', actual.get_item(1).key.value)
        self.assertEqual('meow', actual.get_item(1).value.value)

    def test_record_parser_parse_existing_builder_multiple(self):
        # Given
        message = _InputMessage._create(' pig: oink')
        parser = _ReconParser()
        builder = parser._create_record_builder()
        builder.add(parser._create_slot(Text.create_from('bird'), Text.create_from('chirp')))
        builder.add(parser._create_slot(Text.create_from('dog'), Text.create_from('bark')))
        # When
        actual = parser._parse_record(message, builder=builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(3, actual.size)
        self.assertEqual('bird', actual.get_item(0).key.value)
        self.assertEqual('chirp', actual.get_item(0).value.value)
        self.assertEqual('dog', actual.get_item(1).key.value)
        self.assertEqual('bark', actual.get_item(1).value.value)
        self.assertEqual('pig', actual.get_item(2).key.value)
        self.assertEqual('oink', actual.get_item(2).value.value)

    def test_record_parser_parse_empty(self):
        # Given
        message = _InputMessage._create('')
        parser = _ReconParser()
        # When
        actual = parser._parse_record(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(0, actual.size)
        self.assertEqual(_Absent._get_absent(), actual.value)

    def test_record_parser_parse_block_string(self):
        # Given
        message = '@animals{dog: bark  , cat: meow; bird : chirp}'
        parser = _ReconParser()
        # When
        actual = parser._parse_block_string(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(4, actual.size)
        self.assertEqual('animals', actual._tag)
        self.assertEqual('dog', actual.get_item(1).key.value)
        self.assertEqual('bark', actual.get_item(1).value.value)
        self.assertEqual('cat', actual.get_item(2).key.value)
        self.assertEqual('meow', actual.get_item(2).value.value)
        self.assertEqual('bird', actual.get_item(3).key.value)
        self.assertEqual('chirp', actual.get_item(3).value.value)

    def test_create_ident_true(self):
        # Given
        message = 'true'
        # When
        actual = _ReconParser._create_ident(message)
        # Then
        self.assertIsInstance(actual, Bool)
        self.assertEqual(True, actual.value)

    def test_create_ident_false(self):
        # Given
        message = 'false'
        # When
        actual = _ReconParser._create_ident(message)
        # Then
        self.assertIsInstance(actual, Bool)
        self.assertEqual(False, actual.value)

    def test_create_ident_text(self):
        # Given
        message = 'Dog'
        # When
        actual = _ReconParser._create_ident(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('Dog', actual.value)
