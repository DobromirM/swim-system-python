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
from typing import Union, List, Optional

from ._utils import _ReconUtils, _OutputMessage
from swimos.structures import Attr, Slot, Value, Text, Num, Bool
from swimos.structures._structs import _Absent, _Item, _Extant, _Record


class _ReconWriter:

    @staticmethod
    def _write_text(value: str) -> '_OutputMessage':
        if _ReconUtils._is_ident(value):
            return _IdentWriter._write(value=value)
        else:
            return _StringWriter._write(value=value)

    @staticmethod
    def _write_number(value: Union[int, float]) -> '_OutputMessage':
        return _NumberWriter._write(value=value)

    @staticmethod
    def _write_bool(value: bool) -> '_OutputMessage':
        return _BoolWriter._write(value=value)

    @staticmethod
    def _write_absent() -> '_OutputMessage':
        return _OutputMessage._create()

    def _write_item(self, item: '_Item') -> 'str':

        if isinstance(item, Attr):
            output = self._write_attr(item.key, item.value)
            return output._message
        elif isinstance(item, Slot):
            output = self._write_slot(item.key, item.value)
            return output._message
        elif isinstance(item, Value):
            output = self._write_value(item)
            return output._message

        raise TypeError(f'No Recon serialization for {type(item).__name__}!')

    def _write_attr(self, key: 'Value', value: 'Value') -> '_OutputMessage':
        return _AttrWriter._write(key=key, writer=self, value=value)

    def _write_slot(self, key: 'Value', value: 'Value') -> '_OutputMessage':
        return _SlotWriter._write(key=key, writer=self, value=value)

    def _write_value(self, value: Value) -> '_OutputMessage':
        if isinstance(value, _Record):
            return self._write_record(value)
        elif isinstance(value, Text):
            return self._write_text(value.get_string_value())
        elif isinstance(value, Num):
            return self._write_number(value.get_num_value())
        elif isinstance(value, Bool):
            return self._write_bool(value.get_bool_value())
        elif isinstance(value, _Absent):
            return self._write_absent()

    def _write_record(self, record: '_Record') -> Optional['_OutputMessage']:
        if record.size > 0:
            message = _BlockWriter._write(items=record.get_items(), writer=self, first=True)
            return message


class _AbstractWriter(ABC):
    @staticmethod
    @abstractmethod
    def _write() -> '_OutputMessage':
        """
        Write an Item object into its string representation.

        :return:                - OutputMessage containing the string representation of the Item object.
        """
        raise NotImplementedError


class _BlockWriter(_AbstractWriter):

    @staticmethod
    def _write(items: List[_Item] = None, writer: '_ReconWriter' = None, first: 'bool' = False,
               in_braces: bool = False) -> '_OutputMessage':
        output = _OutputMessage._create()

        for item in items:

            if isinstance(item, Attr):
                item_text = writer._write_item(item)
                output._append(item_text)
            elif isinstance(item, Value) and not isinstance(item, _Record):
                item_text = writer._write_item(item)
                output._append(item_text)
            else:
                if not first:
                    output._append(',')
                elif isinstance(item, Slot):
                    if output._size > 0 and output._last_char != '(':
                        output._append('{')
                        in_braces = True

                item_text = writer._write_item(item)
                output._append(item_text)
                first = False

        if in_braces:
            output._append('}')

        return output


class _AttrWriter(_AbstractWriter):

    @staticmethod
    def _write(key: 'Value' = None, writer: '_ReconWriter' = None, value: 'Value' = None) -> '_OutputMessage':

        output = _OutputMessage._create('@')
        key_text = writer._write_value(key)

        if key_text:
            output._append(key_text)

        if value != _Extant._get_extant() and value is not None:
            output._append('(')
            value_text = writer._write_value(value)
            output._append(value_text)
            output._append(')')

        return output


class _SlotWriter(_AbstractWriter):

    @staticmethod
    def _write(key: Value = None, writer: '_ReconWriter' = None, value: 'Value' = None) -> '_OutputMessage':

        output = _OutputMessage._create()
        key_text = writer._write_value(key)

        if key_text:
            output._append(key_text)

        output._append(':')
        value_text = writer._write_value(value)

        if value_text:
            output._append(value_text)

        return output


class _StringWriter(_AbstractWriter):

    @staticmethod
    def _write(value: str = None) -> '_OutputMessage':
        output = _OutputMessage._create('"')

        if value:
            output._append(value)

        output._append('"')

        return output


class _NumberWriter(_AbstractWriter):

    @staticmethod
    def _write(value: Union[int, float] = None) -> '_OutputMessage':
        output = _OutputMessage()._create()

        if value is not None:
            output._append(value)

        return output


class _BoolWriter(_AbstractWriter):

    @staticmethod
    def _write(value: bool = None) -> '_OutputMessage':

        if value:
            return _OutputMessage._create('true')
        else:
            return _OutputMessage._create('false')


class _IdentWriter(_AbstractWriter):

    @staticmethod
    def _write(value: str = None) -> '_OutputMessage':
        output = _OutputMessage._create()

        if value:
            output._append(value)

        return output
