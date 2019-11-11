import unittest

from aiounittest import async_test

from swimai.recon import ReconParser, InputMessage, OutputMessage
from swimai.recon.parsers import DecimalParser
from swimai.structures import RecordMap, Slot, Text, Attr, Absent, Num


class TestParsers(unittest.TestCase):

    @async_test
    async def test_parse_literal_slot_empty_builder(self):
        # Given
        message = await InputMessage.create('{foo: bar}')
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertIsInstance(actual, RecordMap)
        self.assertIsInstance(actual.get_item(0), Slot)
        self.assertIsInstance(actual.get_item(0).key, Text)
        self.assertEqual('foo', actual.get_item(0).key.value)
        self.assertIsInstance(actual.get_item(0).value, Text)
        self.assertEqual('bar', actual.get_item(0).value.value)

    @async_test
    async def test_parse_literal_slot_existing_builder(self):
        # Given
        message = await InputMessage.create('{Foo: Bar}')
        builder = await ReconParser.create_value_builder()
        builder.add(Attr.create_attr('Baz', 'Qux'))
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message, builder)
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

    @async_test
    async def test_parse_literal_ident_empty_builder(self):
        # Given
        message = await InputMessage.create('foo')
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('foo', actual.value)
        self.assertEqual(Absent.get_absent(), actual.key)

    @async_test
    async def test_parse_literal_ident_existing_builder(self):
        # Given
        message = await InputMessage.create('foo')
        builder = await ReconParser.create_value_builder()
        builder.add(Text.create_from('bar'))
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message, builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(2, actual.size)
        self.assertIsInstance(actual.get_item(0), Text)
        self.assertIsInstance(actual.get_item(1), Text)
        self.assertEqual('bar', actual.get_item(0).value)
        self.assertEqual('foo', actual.get_item(1).value)

    @async_test
    async def test_parse_literal_quote_empty_builder(self):
        # Given
        message = await InputMessage.create('"Baz_Foo"')
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertIsInstance(actual.value, str)
        self.assertEqual('Baz_Foo', actual.value)

    @async_test
    async def test_parse_literal_quote_existing_builder(self):
        # Given
        message = await InputMessage.create('"Hello_World"')
        builder = await ReconParser.create_value_builder()
        parser = ReconParser()
        builder.add(Text.create_from('Hi'))
        builder.add(Text.create_from('Bye'))
        # When
        actual = await parser.parse_literal(message, builder)
        # Then
        self.assertIsInstance(actual, RecordMap)
        self.assertEqual(3, actual.size)
        self.assertIsInstance(actual.get_item(0), Text)
        self.assertIsInstance(actual.get_item(1), Text)
        self.assertIsInstance(actual.get_item(2), Text)
        self.assertEqual('Hi', actual.get_item(0).value)
        self.assertEqual('Bye', actual.get_item(1).value)
        self.assertEqual('Hello_World', actual.get_item(2).value)

    @async_test
    async def test_parse_literal_minus_empty_builder(self):
        # Given
        message = await InputMessage.create('-13.42')
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertIsInstance(actual.value, float)
        self.assertEqual(-13.42, actual.value)

    @async_test
    async def test_parse_literal_minus_existing_builder(self):
        # Given
        message = await InputMessage.create('  37')
        parser = ReconParser()
        builder = await ReconParser.create_value_builder()
        builder.add(Text.create_from('Hello'))
        builder.add(Text.create_from('Friend'))
        # When
        actual = await parser.parse_literal(message, builder)
        # Then
        self.assertEqual(3, actual.size)
        self.assertIsInstance(actual, RecordMap)
        self.assertIsInstance(actual.get_item(0), Text)
        self.assertIsInstance(actual.get_item(1), Text)
        self.assertIsInstance(actual.get_item(2), Num)
        self.assertEqual('Hello', actual.get_item(0).value)
        self.assertEqual('Friend', actual.get_item(1).value)
        self.assertEqual(37, actual.get_item(2).value)

    @async_test
    async def test_parse_literal_empty_empty_builder(self):
        # Given
        message = await InputMessage.create('')
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message)
        # Then
        self.assertEqual(Absent.get_absent(), actual)

    @async_test
    async def test_parse_literal_empty_existing_builder(self):
        # Given
        message = await InputMessage.create('')
        builder = await ReconParser.create_value_builder()
        builder.add(Text.create_from('Hello'))
        parser = ReconParser()
        # When
        actual = await parser.parse_literal(message, builder)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual(0, actual.size)
        self.assertEqual('Hello', actual.value)

    @async_test
    async def test_parse_decimal_positive_empty_value(self):
        # Given
        message = await InputMessage.create('.32')
        parser = ReconParser()
        # When
        actual = await DecimalParser.parse(message, parser)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.32, actual.value)

    @async_test
    async def test_parse_decimal_positive_existing_value(self):
        # Given
        message = await InputMessage.create('.691')
        parser = ReconParser()
        value_output = 12
        # When
        actual = await DecimalParser.parse(message, parser, value_output)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(12.691, actual.value)

    @async_test
    async def test_parse_decimal_negative_empty_value(self):
        # Given
        message = await InputMessage.create('.1')
        parser = ReconParser()
        # When
        actual = await DecimalParser.parse(message, parser, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.1, actual.value)

    @async_test
    async def test_parse_decimal_negative_existing_value(self):
        # Given
        message = await InputMessage.create('.1091')
        parser = ReconParser()
        value_output = -13
        # When
        actual = await DecimalParser.parse(message, parser, value_output, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-13.1091, actual.value)

    @async_test
    async def test_parse_decimal_empty_positive_empty_value(self):
        # Given
        message = await InputMessage.create('')
        parser = ReconParser()
        # When
        actual = await DecimalParser.parse(message, parser)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.0, actual.value)

    @async_test
    async def test_parse_decimal_empty_positive_existing_value(self):
        # Given
        message = await InputMessage.create('')
        parser = ReconParser()
        value_output = 15
        # When
        actual = await DecimalParser.parse(message, parser, value_output)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(15.0, actual.value)

    @async_test
    async def test_parse_decimal_empty_negative_empty_value(self):
        # Given
        message = await InputMessage.create('')
        parser = ReconParser()
        # When
        actual = await DecimalParser.parse(message, parser, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.0, actual.value)

    @async_test
    async def test_parse_decimal_empty_negative_existing_value(self):
        # Given
        message = await InputMessage.create('')
        parser = ReconParser()
        value_output = -16
        # When
        actual = await DecimalParser.parse(message, parser, value_output, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-16.0, actual.value)

    @async_test
    async def test_parse_decimal_dot_only_positive_empty_value(self):
        # Given
        message = await InputMessage.create('.')
        parser = ReconParser()
        # When
        actual = await DecimalParser.parse(message, parser)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.0, actual.value)

    @async_test
    async def test_parse_decimal_dot_only_positive_existing_value(self):
        # Given
        message = await InputMessage.create('.')
        parser = ReconParser()
        value_output = 17
        # When
        actual = await DecimalParser.parse(message, parser, value_output)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(17.0, actual.value)

    @async_test
    async def test_parse_decimal_dot_only_negative_empty_value(self):
        # Given
        message = await InputMessage.create('.')
        parser = ReconParser()
        # When
        actual = await DecimalParser.parse(message, parser, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.0, actual.value)

    @async_test
    async def test_parse_decimal_dot_only_negative_existing_value(self):
        # Given
        message = await InputMessage.create('.')
        parser = ReconParser()
        value_output = -18
        # When
        actual = await DecimalParser.parse(message, parser, value_output, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-18.0, actual.value)

    @async_test
    async def test_parse_number_positive_int(self):
        # Given
        message = await InputMessage.create(' 112')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(112, actual.value)

    @async_test
    async def test_parse_number_negative_int(self):
        # Given
        message = await InputMessage.create('-90')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-90, actual.value)

    @async_test
    async def test_parse_number_positive_float_full(self):
        # Given
        message = await InputMessage.create('91.11')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(91.11, actual.value)

    @async_test
    async def test_parse_number_negative_float_full(self):
        # Given
        message = await InputMessage.create('  -11.12')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-11.12, actual.value)

    @async_test
    async def test_parse_number_positive_float_decimal_only(self):
        # Given
        message = await InputMessage.create('  .12')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0.12, actual.value)

    @async_test
    async def test_parse_number_negative_float_decimal_only(self):
        # Given
        message = await InputMessage.create('  .31')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.31, actual.value)

    @async_test
    async def test_parse_number_float_point_only(self):
        # Given
        message = await InputMessage.create('.')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message, sign_output=-1)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(-0.00, actual.value)

    @async_test
    async def test_parse_number_empty(self):
        # Given
        message = await InputMessage.create('')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(0, actual.value)

    @async_test
    async def test_parse_number_leading_zero(self):
        # Given
        message = await InputMessage.create('012')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(12, actual.value)

    @async_test
    async def test_parse_number_leading_zeroes(self):
        # Given
        message = await InputMessage.create('00013')
        parser = ReconParser()
        # When
        actual = await parser.parse_number(message)
        # Then
        self.assertIsInstance(actual, Num)
        self.assertEqual(13, actual.value)

    @async_test
    async def test_parse_string_normal(self):
        # Given
        message = await InputMessage.create('"Hello, friend"')
        parser = ReconParser()
        # When
        actual = await parser.parse_string(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('Hello, friend', actual.value)

    @async_test
    async def test_parse_string_missing_closing_quote(self):
        # Given
        message = await InputMessage.create('  "Hello, World')
        parser = ReconParser()
        # When
        actual = await parser.parse_string(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('Hello, World', actual.value)

    @async_test
    async def test_parse_string_existing_output(self):
        # Given
        message = await InputMessage.create('"dog"')
        output = await OutputMessage.create('This is ')
        parser = ReconParser()
        # When
        actual = await parser.parse_string(message, output)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('This is dog', actual.value)

    @async_test
    async def test_parse_string_empty(self):
        # Given
        message = InputMessage()
        parser = ReconParser()
        # When
        actual = await parser.parse_string(message)
        # Then
        self.assertIsInstance(actual, Text)
        self.assertEqual('', actual.value)
