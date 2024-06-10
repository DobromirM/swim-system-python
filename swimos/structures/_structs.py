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

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, Optional, Dict, Union


class _Item(ABC):

    def _concat(self, new_item: '_Item') -> '_Record':
        """
        Creates a Record object by appending an Item object to the current Item.

        :param new_item:        - New Item to add to the Record.
        :return:                - Record containing the current Item and the new Item.
        """
        record = _Record.create()
        record.add(self)

        if isinstance(new_item, _Record):
            record._add_all(new_item.get_items())
        else:
            record.add(new_item)

        return record

    @staticmethod
    def create_from(obj: Any) -> '_Item':
        """
        Create Item object from a compatible object.

        :param obj:             - Object extending Item or a dictionary.
        :return:                - Converted object as Item.
        """
        if isinstance(obj, _Item):
            return obj
        elif isinstance(obj, dict) and len(obj) == 1:
            entry = next(iter(obj.items()))
            return Slot.create_slot(entry[0], entry[1])
        else:
            return Value.create_from(obj)

    @staticmethod
    def extant() -> '_Extant':
        """
        Return Extant item singleton.

        :return:                - Item of type Extant.
        """
        return _Extant._get_extant()

    @staticmethod
    def absent() -> '_Absent':
        """
        Return Absent item singleton.

        :return:                - Item of type Absent.
        """
        return _Absent._get_absent()

    @property
    @abstractmethod
    def key(self) -> 'Any':
        raise NotImplementedError

    @property
    @abstractmethod
    def value(self) -> 'Any':
        raise NotImplementedError


class _Field(_Item):

    @property
    @abstractmethod
    def key(self) -> 'Any':
        raise NotImplementedError

    @property
    @abstractmethod
    def value(self) -> 'Any':
        raise NotImplementedError


class Attr(_Field):

    def __init__(self, key: 'Value', value: Any) -> None:
        self.__key = key
        self.__value = value

    def __str__(self) -> str:
        if self.value == Value.extant():
            return f'Attr({self.key})'
        else:
            return f'Attr({self.key}, {self.value})'

    @property
    def key(self) -> 'Value':
        return self.__key

    @property
    def value(self) -> Any:
        return self.__value

    @staticmethod
    def create_attr(key: Any, value: Any) -> 'Attr':
        """
        Create an attribute object from given key and value.

        :param key:             - Key of the attribute. Can be Text or str.
        :param value:           - Value of the attribute.
        :return:                - Attribute object.
        """
        if key is None:
            raise TypeError('Empty key for attribute!')

        if value is None:
            raise TypeError('Empty value for attribute!')

        if isinstance(key, Text):
            return Attr(key, value)
        elif isinstance(key, str):
            return Attr(Text.create_from(key), value)
        else:
            raise TypeError(f'Invalid key: {key}')

    def key_equals(self, item: Any) -> bool:
        """
        Compare the key of the attribute to an arbitrary object.

        :param item:            - Item to compare the key to.
        :return:                - True if the key and the item are equal, False otherwise.
        """
        if isinstance(item, str):
            return self.key.value == item
        elif isinstance(item, _Field):
            return self.key.value == item.key.value
        else:
            return self.key.value == item


class Value(_Item):

    @property
    def key(self) -> 'Value':
        return Value.absent()

    @property
    def value(self) -> 'Value':
        return Value.absent()

    @property
    def size(self) -> int:
        return 0

    @staticmethod
    def create_from(obj: Any) -> 'Value':
        """
        Create Value object from a compatible object.

        :param obj:             - Object extending Value or None.
        :return:                - Converted object as Value.
        """

        if obj is None:
            return _Extant._get_extant()
        elif isinstance(obj, Value):
            return obj
        elif isinstance(obj, str):
            return Text.create_from(obj)
        elif isinstance(obj, bool):
            return Bool.create_from(obj)
        elif isinstance(obj, (float, int)):
            return Num.create_from(obj)
        else:
            raise TypeError(f'{str(obj)} cannot be converted to Value!')


class Text(Value):
    empty = None

    def __init__(self, value: str) -> None:
        self.__value = value

    def __str__(self) -> str:
        return f'"{self.value}"'

    @property
    def value(self) -> str:
        return self.__value

    @staticmethod
    def create_from(string: str) -> 'Text':
        """
        Create Text object from a string.

        :param string:          - String value.
        :return:                - Converted string as a Text object.
        """
        if not isinstance(string, str):
            raise Exception('Cannot create a Text object with non string value!')

        if not string:
            return Text.get_empty()
        return Text(string)

    @staticmethod
    def get_empty() -> 'Text':
        """
        Create an empty Text singleton if it does not exist and return it.

        :return:                - Empty Text singleton.
        """
        if Text.empty is None:
            Text.empty = Text('')

        return Text.empty

    def get_string_value(self) -> str:
        """
        Return the value of the Text object as string.

        :return:                - Text value as string.
        """
        return self.value


class Num(Value):

    def __init__(self, value: Union[int, float]) -> None:
        self.__value = value

    def __str__(self) -> str:
        return str(self.value)

    @property
    def value(self) -> Union[int, float]:
        return self.__value

    @staticmethod
    def create_from(obj: Union[float, int]) -> 'Num':
        """
        Create Num object from a compatible object.

        :param obj:             - Integer or Float value.
        :return:                - Converted value as a Num object.
        """

        if not isinstance(obj, (float, int)):
            raise Exception('Cannot create a Num object with non numeric value!')

        return Num(obj)

    def get_num_value(self) -> Union[int, float]:
        """
        Return the value of the Num object as integer or float.

        :return:                - Num value as integer or float.
        """
        return self.value


class Bool(Value):
    _TRUE = None
    _FALSE = None

    def __init__(self, value: bool) -> None:
        self.__value = value

    def __str__(self) -> str:
        return str(self.value)

    def __bool__(self) -> bool:
        return self.value

    @property
    def value(self) -> bool:
        return self.__value

    @staticmethod
    def create_from(obj: bool) -> 'Bool':
        """
        Create Bool object from a compatible object.

        :param obj:             - Boolean value.
        :return:                - Converted value as a Bool object.
        """

        if obj:
            if Bool._TRUE is None:
                Bool._TRUE = Bool(True)

            return Bool._TRUE
        else:
            if Bool._FALSE is None:
                Bool._FALSE = Bool(False)

            return Bool._FALSE

    def get_bool_value(self) -> bool:
        """
        Return the value of the Bool object as Boolean.

        :return:                - Bool value as Boolean.
        """
        return self.value


class _Absent(Value):
    _absent = None

    def __str__(self) -> str:
        return 'Absent()'

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def _get_absent() -> '_Absent':
        """
        Create an Absent singleton if it does not exist and return it

        :return:                - Absent singleton.
        """
        if _Absent._absent is None:
            _Absent._absent = _Absent()

        return _Absent._absent


class _Extant(Value):
    extant = None

    def __str__(self) -> str:
        return 'Extant()'

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def _get_extant() -> '_Extant':
        """
        Create an Extant singleton if it does not exist and return it

        :return:                - Extant singleton.
        """
        if _Extant.extant is None:
            _Extant.extant = _Extant()

        return _Extant.extant


class Slot(_Field):

    def __init__(self, key: Any, value: Any = Value.extant()) -> None:
        self.__key = key
        self.__value = value

    def __str__(self) -> str:
        return f'Slot({self.key}, {self.value})'

    @property
    def key(self) -> Any:
        return self.__key

    @property
    def value(self) -> Any:
        return self.__value

    @staticmethod
    def create_slot(key: Any, value: Any = None) -> 'Slot':
        """
        Create a slot object from given key and value (optional).

        :param key:             - Key for the slot.
        :param value:           - Value for the slot. Defaults to Extant.
        :return:                - Slot object.
        """

        if key is None:
            raise TypeError('Empty key for slot!')

        if value is None:
            value = Value.extant()

        return Slot(key, value)


class _RecordFlags(Enum):
    """
    IMMUTABLE(1), ALIASED(2)
    """
    IMMUTABLE = 1 << 0
    ALIASED = 1 << 1


class _Record(Value):

    def __str__(self) -> str:

        string = f'Record({", ".join([str(item) for item in self.get_items()])})'
        return string

    @staticmethod
    def create() -> 'RecordMap':
        """
        Create a new RecordMap.
        :return:                - The newly crated RecordMap.
        """
        return RecordMap.create()

    @abstractmethod
    def add(self, item) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_item(self, index: int) -> 'Value':
        """
        Return an item with a given index from the Record.

        :param index:           - The index of the item.
        :return:                - The item with the given index.
        """
        raise NotImplementedError

    @abstractmethod
    def get_items(self) -> List['Value']:
        """
        Return all items from the Record.

        :return:                - List of all items from the Record.
        """
        raise NotImplementedError

    def _add_all(self, items: List['Value']) -> bool:
        """
        Add a list of items to the Record.

        :param items:           - List of items to be added.
        :return:                - True if at least one item has been added. False otherwise.
        """
        changed = False

        for item in items:
            self.add(item)
            changed = True

        return changed

    def _add_slot(self, key: Any, value: Any) -> '_Record':
        """
        Add a Slot to the Record.

        :param key:             - Key for the slot object.
        :param value:           - Value for the slot object.
        :return:                - The current Record with the added Slot.
        """
        if isinstance(key, str):
            key = Text.create_from(key)

        if isinstance(value, str):
            value = Text.create_from(value)

        self.add(Slot.create_slot(key, value))

        return self

    def _get_headers(self, tag: str) -> Optional['_Record']:
        """
        Return a Record of all headers for a given tag.

        :param tag:             - Tag of the header Record.
        :return:                - Record of all headers or None.
        """
        head = self._get_head()

        if isinstance(head, Attr) and head.key_equals(tag):
            header = head.value
            if isinstance(header, _Record):
                return header
            else:
                return RecordMap.create_record_map(header)
        else:
            return None

    def _get_head(self) -> '_Item':
        """
        Return the first item from the Record if it exists.

        :return:                - First item in the Record.
        """
        return self.get_item(0)

    def _bind(self) -> '_Record':
        """
        Return a Record object.

        :return:                - Return itself.
        """
        return self


class RecordMap(_Record):

    def __init__(self, items: List[_Item] = None, fields: Dict[str, _Item] = None, item_count: int = 0,
                 field_count: int = 0, flags: int = 0) -> None:
        self._items = items
        self._fields = fields
        self._item_count = item_count
        self._field_count = field_count
        self._flags = flags

    @property
    def size(self) -> int:
        return self._item_count

    @staticmethod
    def create() -> 'RecordMap':
        """
        Create an empty RecordMap.

        :return:                - Empty RecordMap.
        """
        items = list()
        return RecordMap(items, flags=_RecordFlags.ALIASED.value)

    @staticmethod
    def create_record_map(obj: Any) -> 'RecordMap':
        """
        Create RecordMap and add a given object.

        :param obj:             - Object to add to the new RecordMap.
        :return:                - RecordMap with an object.
        """
        array = list()
        item = _Item.create_from(obj)
        array.append(item)

        field_count = 1 if isinstance(item, _Field) else 0

        return RecordMap(array, None, 1, field_count, 0)

    def get_item(self, index: int) -> _Item:
        """
        Return an item with a given index from the RecordMap.

        :param index:           - The index of the item.
        :return:                - The item with the given index or Absent if the index is out of bounds.
        """
        if 0 <= index < self._item_count:
            return self._items[index]
        else:
            return _Item.absent()

    def get_items(self) -> List[_Item]:
        """
        Return all items from the RecordMap.

        :return:                - List of all items from the RecordMap.
        """
        return self._items

    def get_body(self) -> _Item:
        """
        Return the body of the RecordMap.

        :return:                - Value or RecordMap representing the body of the RecordMap.
        """
        n = self._item_count

        if n > 2:
            return _RecordMapView(self, 1, n)._branch()
        elif n == 2:
            item = self._items[1]

            if isinstance(item, Value):
                return item
            else:
                return RecordMap.create_record_map(item)

        else:
            return Value.absent()

    def add(self, item: _Item) -> bool:
        """
        Add an item to the RecordMap.

        :param item:            - Item to add to the RecordMap.
        :return:                - True if the item was successfully added.
        """
        if self._flags & _RecordFlags.IMMUTABLE.value:
            raise TypeError('Cannot add item to immutable record!')
        if self._flags & _RecordFlags.ALIASED.value:
            return self.__add_aliased(item)
        else:
            return self.__add_mutable(item)

    def commit(self) -> 'RecordMap':
        """
        Make the RecordMap read-only and return it.

        :return:                - Read-only RecordMap.
        """
        self._flags |= _RecordFlags.IMMUTABLE.value
        return self

    def contains_key(self, key: Any) -> bool:
        """
        Check if a given key exists in the RecordMap.

        :param key:             - Key to check.
        :return:                - True if the key exists, False otherwise.
        """
        key = Value.create_from(key).value

        if self._field_count != 0:
            self.__init_hash_table()

            return key in self._fields

        return False

    @property
    def _tag(self) -> Optional[str]:
        """
        Return the tag of the RecordMap.

        :return:                - The tag of the RecordMap or None.
        """
        if self._field_count > 0:
            item = self._items[0]
            if isinstance(item, Attr):
                return str(item.key.value)

        return None

    def _branch(self) -> 'RecordMap':
        """
        Create a copy of the current RecordMap. The copies reference a shared object
        until one of them is mutated.

        :return:                - Copy of a RecordMap.
        """
        self._flags |= _RecordFlags.ALIASED.value
        return RecordMap(self._items, self._fields, self._item_count, self._field_count, _RecordFlags.ALIASED.value)

    def __add_mutable(self, item: _Item) -> bool:
        """
        Add an item to a mutable RecordMap.

        :param item:            - Item to add to the RecordMap.
        :return:                - True if the item was successfully added.
        """
        self._items = self._items[:]
        self._items.append(item)
        self._item_count = self._item_count + 1

        if isinstance(item, _Field):
            self._field_count += 1

            if self._fields is not None:
                self._fields[item.key.value] = item
            else:
                self._fields = None

        return True

    def __add_aliased(self, item: _Item) -> bool:
        """
        Add an item to an aliased RecordMap.

        :param item:            - Item to add to the RecordMap.
        :return:                - True if the item was successfully added.
        """
        self._items = self._items[:]
        self._items.append(item)
        self._item_count = self._item_count + 1

        if isinstance(item, _Field):
            self._field_count += 1

        self._fields = None
        self._flags &= ~_RecordFlags.ALIASED.value
        return True

    def __init_hash_table(self) -> None:
        """
        Create a hashtable and all items from the RecordMap.
        """
        self._fields = dict()
        for item in self._items:
            self._fields[item.key.value] = item


class _RecordMapView(_Record):

    def __init__(self, record: RecordMap, lower: int, upper: int) -> None:
        self._record = record
        self._lower = lower
        self._upper = upper

    @property
    def size(self) -> int:
        return self._upper - self._lower

    def get_item(self, index: int) -> _Item:
        """
        Return an item with a given index from the RecordMapView.

        :param index:           - The index of the item.
        :return:                - The item with the given index or Absent if the index is out of bounds.
        """
        if 0 <= index < self.size:
            return self._record._items[self._lower + index]
        else:
            return _Item.absent()

    def get_items(self) -> List[_Item]:
        """
        Return all items from the RecordMapView.

        :return:                - List of all items from the RecordMapView.
        """
        return self._record._items[self._lower: self._upper]

    def add(self, item: _Item, index: int = None) -> bool:
        """
         Add an item to the underlying RecordMap at a given index.

         :param item:           - Item to add to the RecordMapView.
         :param index:          - Index of the position at which the item should be added.
         :return:               - True if the item was successfully added.
         """
        if index is None:
            index = self.size

        if self._record._flags & _RecordFlags.IMMUTABLE.value:
            raise TypeError('Cannot add item to immutable record!')
        elif index < 0 or index > self.size:
            raise IndexError(f'Index {index} is out of range!')
        else:
            self.__add_item(index, item)

        return True

    def _branch(self) -> RecordMap:
        """
        Create a copy of the underlying RecordMap.

        :return:                - Copy of the underlying RecordMap.
        """
        size = self.size
        fields_count = 0
        copy_index = self._lower
        new_array = list()

        for _ in range(0, size):

            item = self._record._items[copy_index]
            new_array.append(item)

            if isinstance(item, _Field):
                fields_count += 1

            copy_index += 1

        return RecordMap(new_array, None, size, fields_count, 0)

    def __add_item(self, index: int, item: _Item) -> None:
        """
        Add an item to the underlying RecordMapView.

        :param index:           - Index of the position at which the item should be added.
        :param item:            - Item to add to the RecordMapView.
        """
        lower = self._lower + index
        self._record._items = self._record._items[0: lower] + [item] + self._record._items[
                                                                       lower: self._record.size - lower]
        self._record._fields = None
        self._record._item_count += 1

        if isinstance(item, _Field):
            self._record._field_count += 1

        self._record._flags = self._record._flags & ~_RecordFlags.ALIASED.value
        self._upper += 1


class _ValueBuilder:

    def __init__(self) -> None:
        self._record = None
        self._value = None

    def add(self, item: _Item) -> bool:
        """
        Add an item to the ValueBuilder.

        :param item:            - Item to add to the ValueBuilder.
        :return:                - True if the item was successfully added.
        """
        if isinstance(item, _Field):
            return self.__add_field(item)
        elif isinstance(item, Value):
            return self.__add_value(item)
        else:
            raise TypeError(f'Item of type {type(item).__name__} is not supported by the Value Builder')

    def _bind(self) -> Value:
        """
        Return the contents of the ValueBuilder as a Value object.

        :return:                - The built Value from the ValueBuilder.
        """
        if self._record is not None:
            return self._record
        elif self._value is not None:
            return self._value
        else:
            return Value.absent()

    def __add_field(self, item: _Field) -> bool:
        """
        Add a field to the ValueBuilder.

        :param item:            - Field to add to the ValueBuilder.
        :return:                - True if the Field was successfully added.
        """
        if self._record is None:
            self._record = _Record.create()

            if self._value is not None:
                self._record.add(self._value)
                self._value = None

        self._record.add(item)
        return True

    def __add_value(self, item: Value) -> bool:
        """
        Add a Value to the ValueBuilder.

        :param item:            - Value to add to the ValueBuilder.
        :return:                - True if the Value was successfully added.
        """
        if self._record is not None:
            self._record.add(item)
        elif self._value is None:
            self._value = item
        else:
            self._record = _Record.create()
            self._record.add(self._value)
            self._value = None
            self._record.add(item)

        return True


class RecordConverter:
    _converter = None

    @staticmethod
    def get_converter() -> 'RecordConverter':
        """
        Create a Record Converter singleton if it does not exist and return it.

        :return:                - Record Converter singleton.
        """
        if RecordConverter._converter is None:
            RecordConverter._converter = RecordConverter()

        return RecordConverter._converter

    def object_to_record(self, obj: Any) -> '_Item':
        """
        Convert an object into a Recon record.

        :param obj:             - Object to convert.
        :return:                - Recon record representing the original object.
        """

        if obj is None:
            return RecordMap.create()

        if isinstance(obj, _Item):
            return obj

        if isinstance(obj, (str, float, int, bool)):
            record = Value.create_from(obj)

        elif isinstance(obj, dict):
            record = RecordMap.create()
            self.__process_entries(obj, record)

        else:
            record = RecordMap.create()
            attr_value = Text.create_from(obj.__class__.__name__)
            record.add(Attr.create_attr(attr_value, _Extant._get_extant()))
            self.__process_entries(obj.__dict__, record)

        return record

    def record_to_object(self, record: '_Record', classes: dict, strict: bool) -> 'Any':
        """
        Convert a Recon record into an object.

        :param record:          - Recon record to convert.
        :param classes:         - Specific Python classes to use in the conversion.
        :param strict:          - Boolean flag indicating if the conversion should fail if a needed class is not
                                  explicitly provided.
        :return:                - The newly created object.
        """
        if isinstance(record, _Absent):
            return Value.absent()
        if isinstance(record, (Text, Num, Bool)):
            return record.value
        if isinstance(record, _Record) and isinstance(record._get_head(), Attr):
            new_object = self.__record_to_class(record, classes, strict)
        else:
            new_object = self.__record_to_dict(record, classes, strict)

        return new_object

    def __process_entries(self, entries: dict, record: '_Record') -> None:
        """
        Convert entries to Recon and add them to the main record.

        :param entries:         - Dictionary of entries to convert.
        :param record:          - Main record for appending the converted entries.
        """
        for key, value in entries.items():

            if value is not None:
                slot_value = self.object_to_record(value)
                key_value = Text.create_from(key)
                record.add(Slot.create_slot(key_value, slot_value))

    @staticmethod
    def __attr_to_object(attribute: _Item, classes: dict, strict: bool) -> Any:
        """
        Convert a Recon attribute item to a Python object.

        :param attribute:       - Recon attribute item to convert.
        :param classes:         - Specific Python classes to use in the conversion.
        :param strict:          - Boolean flag indicating if the conversion should fail if a needed class is not
                                  explicitly provided.
        :return:                - The newly created object.
        """

        class_name = attribute.key.value
        class_object = classes.get(class_name)

        if class_object is not None:
            return class_object()
        elif not strict:
            dynamic_type = type(str(class_name), (object,), {})
            return dynamic_type()
        else:
            raise Exception(f'Missing class for {class_name}.')

    def __record_to_class(self, record: '_Record', classes: dict, strict: bool) -> Any:
        """
        Convert a Recon record to an instance of a Python class.

        :param record:          - Recon record to convert.
        :param classes:         - Specific Python classes to use in the conversion.
        :param strict:          - Boolean flag indicating if the conversion should fail if a needed class is not
                                  explicitly provided.
        :return:                - The newly created object.
        """

        new_object = self.__attr_to_object(record._get_head(), classes, strict)

        items_iter = iter(record.get_items())
        next(items_iter)

        for item in items_iter:
            record = item.value
            attribute = str(item.key.value)

            if strict:
                if not hasattr(new_object, attribute):
                    raise Exception(f'Missing attribute {attribute} for class {type(new_object).__name__}.')

            if isinstance(record, RecordMap):
                setattr(new_object, attribute, self.record_to_object(record, classes, strict))
            else:
                setattr(new_object, attribute, item.value.value)

        return new_object

    def __record_to_dict(self, record: '_Record', classes: dict, strict: bool) -> dict:
        """
        Convert a Recon record to a Python dictionary.

        :param record:          - Recon record to convert.
        :param classes:         - Specific Python classes to use in the conversion.
        :param strict:          - Boolean flag indicating if the conversion should fail if a needed class is not
                                  explicitly provided.
        :return:                - The newly created dictionary.
        """
        new_object = dict()

        for item in record.get_items():
            value = item.key.value
            if isinstance(value, RecordMap):
                new_object[item.key.key.value] = self.record_to_object(value, classes, strict)
            else:
                new_object[item.key.value] = item.value.value

        return new_object
