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

from swimos.recon._parsers import _OutputMessage
from swimos.recon._writers import _BoolWriter, _IdentWriter, _NumberWriter, _StringWriter, _SlotWriter, _ReconWriter, \
    _AttrWriter, _BlockWriter
from swimos.structures import Text, Slot, Attr, Num, Bool
from swimos.structures._structs import _Extant, _Absent, _Record
from test.utils import CustomItem


class TestWriters(unittest.TestCase):

    def test_ident_writer_str(self):
        # Given
        message = 'hello'
        # When
        actual = _IdentWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('hello', actual._value)

    def test_ident_writer_empty(self):
        # Given
        message = ''
        # When
        actual = _IdentWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('', actual._value)

    def test_bool_writer_true(self):
        # Given
        message = True
        # When
        actual = _BoolWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('true', actual._value)

    def test_bool_writer_false(self):
        # Given
        message = False
        # When
        actual = _BoolWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('false', actual._value)

    def test_bool_writer_none(self):
        # Given
        message = None
        # When
        actual = _BoolWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('false', actual._value)

    def test_number_writer_zero(self):
        # Given
        message = 0
        # When
        actual = _NumberWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('0', actual._value)

    def test_number_writer_int(self):
        # Given
        message = 25
        # When
        actual = _NumberWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('25', actual._value)

    def test_number_writer_float(self):
        # Given
        message = 0.02
        # When
        actual = _NumberWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('0.02', actual._value)

    def test_number_writer_none(self):
        # Given
        message = None
        # When
        actual = _NumberWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('', actual._value)

    def test_string_writer_str(self):
        # Given
        message = 'This is dog'
        # When
        actual = _StringWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('"This is dog"', actual._value)

    def test_string_writer_empty(self):
        # Given
        message = None
        # When
        actual = _StringWriter._write(message)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('""', actual._value)

    def test_slot_writer_existing_key_and_value(self):
        # Given
        key = Text.create_from('animal')
        value = Text.create_from('dog')
        writer = _ReconWriter()
        # When
        actual = _SlotWriter._write(key=key, writer=writer, value=value)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('animal:dog', actual._value)

    def test_slot_writer_existing_key_missing_value(self):
        # Given
        key = Text.create_from('animal')
        writer = _ReconWriter()
        # When
        actual = _SlotWriter._write(key=key, writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('animal:', actual._value)

    def test_slot_writer_missing_key_existing_value(self):
        # Given
        value = Text.create_from('dog')
        writer = _ReconWriter()
        # When
        actual = _SlotWriter._write(value=value, writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(':dog', actual._value)

    def test_slot_writer_missing_key_and_value(self):
        # Given
        writer = _ReconWriter()
        # When
        actual = _SlotWriter._write(writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(':', actual._value)

    def test_attr_writer_existing_key_and_value_text(self):
        # Given
        key = Text.create_from('bird')
        value = Text.create_from('chirp')
        writer = _ReconWriter()
        # When
        actual = _AttrWriter._write(key=key, writer=writer, value=value)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@bird(chirp)', actual._message)

    def test_attr_writer_existing_key_and_value_slot(self):
        # Given
        key = Text.create_from('animal')
        value = _Record.create()
        value.add(Slot.create_slot(Text.create_from('dog'), Text.create_from('bark')))
        writer = _ReconWriter()
        # When
        actual = _AttrWriter._write(key=key, writer=writer, value=value)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@animal(dog:bark)', actual._message)

    def test_attr_writer_missing_key_existing_value(self):
        # Given
        value = Text.create_from('chirp')
        writer = _ReconWriter()
        # When
        actual = _AttrWriter._write(writer=writer, value=value)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@(chirp)', actual._message)

    def test_attr_writer_existing_key_missing_value(self):
        # Given
        key = Text.create_from('bird')
        writer = _ReconWriter()
        # When
        actual = _AttrWriter._write(key=key, writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@bird', actual._message)

    def test_attr_writer_existing_key_extant_value(self):
        # Given
        key = Text.create_from('bird')
        value = _Extant._get_extant()
        writer = _ReconWriter()
        # When
        actual = _AttrWriter._write(key=key, writer=writer, value=value)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@bird', actual._message)

    def test_attr_writer_missing_key_and_value(self):
        # Given
        writer = _ReconWriter()
        # When
        actual = _AttrWriter._write(writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@', actual._message)

    def test_block_writer_attr(self):
        # Given
        items = list()
        items.append(Attr.create_attr(Text.create_from('dog'), Text.create_from('bark')))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@dog(bark)', actual._message)

    def test_block_writer_text_single(self):
        # Given
        items = list()
        items.append(Text.create_from('Dead parrot'))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('"Dead parrot"', actual._message)

    def test_block_writer_text_multiple(self):
        # Given
        items = list()
        items.append(Text.create_from('foo_'))
        items.append(Text.create_from('bar'))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('foo_bar', actual._message)

    def test_block_writer_slot_single_first(self):
        # Given
        items = list()
        items.append(Slot.create_slot(Text.create_from('cat'), Text.create_from('meow')))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer, first=True)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('cat:meow', actual._message)

    def test_block_writer_slot_single_not_first(self):
        # Given
        items = list()
        items.append(Slot.create_slot(Text.create_from('cat'), Text.create_from('meow')))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer, first=False)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(',cat:meow', actual._message)

    def test_block_writer_slot_multiple(self):
        # Given
        items = list()
        items.append(Slot.create_slot(Text.create_from('dog'), Text.create_from('bark')))
        items.append(Slot.create_slot(Text.create_from('cat'), Text.create_from('meow')))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer, first=True)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('dog:bark,cat:meow', actual._message)

    def test_block_writer_slot_in_attr(self):
        # Given
        items = list()
        record_map = _Record.create()
        record_map.add(Slot.create_slot(Text.create_from('cat'), Text.create_from('meow')))
        items.append(Attr.create_attr(Text.create_from('animal'), record_map))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer, first=True)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@animal(cat:meow)', actual._message)

    def test_block_writer_slot_in_attr_and_slot(self):
        # Given
        items = list()
        record_map = _Record.create()
        record_map.add(Slot.create_slot(Text.create_from('dog'), Text.create_from('bark')))
        items.append(Attr.create_attr(Text.create_from('animal'), record_map))
        items.append(Slot.create_slot(Text.create_from('cat'), Text.create_from('meow')))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer, first=True)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@animal(dog:bark){cat:meow}', actual._message)

    def test_block_writer_multiple_attributes(self):
        # Given
        items = list()

        record_map = _Record.create()

        dog_map = _Record.create()
        dog_map.add(Slot.create_slot(Text.create_from('dog'), Text.create_from('bark')))
        record_map.add(Attr.create_attr(Text.create_from('Animal'), dog_map))

        cat_map = _Record.create()
        cat_map.add(Slot.create_slot(Text.create_from('cat'), Text.create_from('meow')))
        record_map.add(Attr.create_attr(Text.create_from('Animal'), cat_map))

        bird_map = _Record.create()
        bird_map.add(Slot.create_slot(Text.create_from('bird'), Text.create_from('chirp')))
        record_map.add(Attr.create_attr(Text.create_from('Animal'), bird_map))

        items.append(record_map)
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer, first=True)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@Animal(dog:bark)@Animal(cat:meow)@Animal(bird:chirp)', actual._message)

    def test_block_writer_nested_attributes(self):
        # Given
        items = list()
        name_record = _Record.create()
        name_record.add(Slot.create_slot(Text.create_from('Name'), Text.create_from('Collie')))
        breed_record = _Record.create()
        breed_record.add(Attr.create_attr(Text.create_from('Breed'), name_record))
        dog_record = _Record.create()
        dog_record.add(Slot.create_slot(Text.create_from('Dog'), breed_record))
        species_record = _Record.create()
        species_record.add(Attr.create_attr(Text.create_from('Species'), dog_record))
        animals_record = _Record.create()
        animals_record.add(Slot.create_slot(Text.create_from('Animals'), species_record))
        items.append(Attr.create_attr(Text.create_from('Zoo'), animals_record))
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer, first=True)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('@Zoo(Animals:@Species(Dog:@Breed(Name:Collie)))', actual._message)

    def test_block_writer_empty(self):
        # Given
        items = list()
        writer = _ReconWriter()
        # When
        actual = _BlockWriter._write(items, writer=writer)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual('', actual._message)

    def test_write_record_single(self):
        # Given
        record = _Record.create()
        record.add(Text.create_from('Dog'))
        writer = _ReconWriter()
        # When
        actual = writer._write_record(record)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(3, actual._size)
        self.assertEqual('Dog', actual._value)
        self.assertEqual('g', actual._last_char)

    def test_write_record_multiple(self):
        # Given
        record = _Record.create()
        record.add(Text.create_from('Dog'))
        record.add(Text.create_from('Cat'))
        writer = _ReconWriter()
        # When
        actual = writer._write_record(record)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(6, actual._size)
        self.assertEqual('DogCat', actual._value)
        self.assertEqual('t', actual._last_char)

    def test_write_record_empty(self):
        # Given
        record = _Record.create()
        writer = _ReconWriter()
        # When
        actual = writer._write_record(record)
        # Then
        self.assertIsNone(actual)

    def test_write_value_record(self):
        # Given
        record = _Record.create()
        record.add(Slot.create_slot(Text.create_from('Cow'), Text.create_from('Moo')))
        writer = _ReconWriter()
        # When
        actual = writer._write_value(record)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(7, actual._size)
        self.assertEqual('Cow:Moo', actual._value)
        self.assertEqual('o', actual._last_char)

    def test_write_value_text_ident(self):
        # Given
        ident = Text.create_from('Duck')
        writer = _ReconWriter()
        # When
        actual = writer._write_value(ident)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(4, actual._size)
        self.assertEqual('Duck', actual._value)
        self.assertEqual('k', actual._last_char)

    def test_write_value_text_string(self):
        # Given
        string = Text.create_from('$duck')
        writer = _ReconWriter()
        # When
        actual = writer._write_value(string)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(7, actual._size)
        self.assertEqual('"$duck"', actual._value)
        self.assertEqual('"', actual._last_char)

    def test_write_value_number(self):
        # Given
        number = Num.create_from(-13.1)
        writer = _ReconWriter()
        # When
        actual = writer._write_value(number)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(5, actual._size)
        self.assertEqual('-13.1', actual._value)
        self.assertEqual('1', actual._last_char)

    def test_write_value_bool(self):
        # Given
        boolean = Bool.create_from(False)
        writer = _ReconWriter()
        # When
        actual = writer._write_value(boolean)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(5, actual._size)
        self.assertEqual('false', actual._value)
        self.assertEqual('e', actual._last_char)

    def test_write_value_absent(self):
        # Given
        absent = _Absent._get_absent()
        writer = _ReconWriter()
        # When
        actual = writer._write_value(absent)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(0, actual._size)
        self.assertEqual('', actual._value)

    def test_write_slot(self):
        # Given
        key = Text.create_from('Hello')
        value = Text.create_from('Friend')
        writer = _ReconWriter()
        # When
        actual = writer._write_slot(key, value)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(12, actual._size)
        self.assertEqual('Hello:Friend', actual._value)
        self.assertEqual('d', actual._last_char)

    def test_write_attr(self):
        # Given
        key = Text.create_from('Hello')
        value = Text.create_from('Friend')
        writer = _ReconWriter()
        # When
        actual = writer._write_attr(key, value)
        # Then
        self.assertIsInstance(actual, _OutputMessage)
        self.assertEqual(14, actual._size)
        self.assertEqual('@Hello(Friend)', actual._value)
        self.assertEqual(')', actual._last_char)

    def test_write_item_attr(self):
        # Given
        item = Attr.create_attr(Text.create_from('Cat'), Text.create_from('Meow'))
        writer = _ReconWriter()
        # When
        actual = writer._write_item(item)
        # Then
        self.assertIsInstance(actual, str)
        self.assertEqual('@Cat(Meow)', actual)

    def test_write_item_slot(self):
        # Given
        item = Slot.create_slot(Text.create_from('Age'), Num.create_from(32))
        writer = _ReconWriter()
        # When
        actual = writer._write_item(item)
        # Then
        self.assertIsInstance(actual, str)
        self.assertEqual('Age:32', actual)

    def test_write_item_value(self):
        # Given
        item = Text.create_from('Horse#')
        writer = _ReconWriter()
        # When
        actual = writer._write_item(item)
        # Then
        self.assertIsInstance(actual, str)
        self.assertEqual('"Horse#"', actual)

    def test_write_item_invalid(self):
        # Given
        item = CustomItem()
        writer = _ReconWriter()
        # When
        with self.assertRaises(TypeError) as error:
            writer._write_item(item)

        # Then
        message = error.exception.args[0]
        self.assertEqual('No Recon serialization for CustomItem!', message)
