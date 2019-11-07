from abc import ABC, abstractmethod
from typing import Union, List

from .utils import ReconUtils, OutputMessage
from swimai.structures import Field, Attr, Slot, Value, Record, Text, Absent, Num, Extant, Bool, Item


class ReconWriter:

    @staticmethod
    async def write_text(value: str) -> 'OutputMessage':
        if await ReconUtils.is_ident(value):
            return await IdentWriter.write(value=value)
        else:
            return await StringWriter.write(value=value)

    @staticmethod
    async def write_number(value: Union[int, float]) -> 'OutputMessage':
        return await NumberWriter.write(value=value)

    @staticmethod
    async def write_bool(value: bool) -> 'OutputMessage':
        return await BoolWriter.write(value=value)

    @staticmethod
    async def write_absent() -> 'OutputMessage':
        return await OutputMessage.create()

    async def write_item(self, item: 'Item') -> 'str':

        if isinstance(item, Field):
            if isinstance(item, Attr):
                output = await self.write_attr(item.key, item.value)
                return output.message
            elif isinstance(item, Slot):
                output = await self.write_slot(item.key, item.value)
                return output.message
        elif isinstance(item, Value):
            output = await self.write_value(item)
            return output.message

        raise AttributeError(f'No Recon serialization for {item}')

    async def write_attr(self, key: 'Value', value: 'Value') -> 'OutputMessage':
        return await AttrWriter.write(key=key, writer=self, value=value)

    async def write_slot(self, key: 'Value', value: 'Value') -> 'OutputMessage':
        return await SlotWriter.write(key=key, writer=self, value=value)

    async def write_value(self, value: Value) -> 'OutputMessage':
        if isinstance(value, Record):
            return await self.write_record(value)
        elif isinstance(value, Text):
            return await self.write_text(value.get_string_value())
        elif isinstance(value, Num):
            return await self.write_number(value.get_num_value())
        elif isinstance(value, Bool):
            return await self.write_bool(value.get_bool_value())
        elif isinstance(value, Absent):
            return await self.write_absent()

    async def write_record(self, record: 'Record') -> 'OutputMessage':
        if record.size > 0:
            message = await BlockWriter.write(items=record.get_items(), writer=self, first=True)
            return message


class Writer(ABC):
    @staticmethod
    @abstractmethod
    async def write() -> 'OutputMessage':
        """
        Write an Item object into its string representation.

        :return:                - OutputMessage containing the string representation of the Item object.
        """
        ...


class BlockWriter(Writer):

    @staticmethod
    async def write(items: List[Value] = None, writer: 'ReconWriter' = None, first: 'bool' = False,
                    in_braces: bool = False) -> 'OutputMessage':
        output = await OutputMessage.create()

        for item in items:

            if isinstance(item, Attr):
                item_text = await writer.write_item(item)
            elif isinstance(item, Value) and not isinstance(item, Record):
                item_text = await writer.write_item(item)
            else:
                if not first:
                    await output.append(',')
                elif isinstance(item, Slot):
                    if output.size > 0 and output.last_char != '(':
                        await output.append('{')
                        in_braces = True

                item_text = await writer.write_item(item)

                first = False

            if item_text:
                await output.append(item_text)

        if in_braces:
            await output.append('}')

        return output


class AttrWriter(Writer):

    @staticmethod
    async def write(key: 'Value' = None, writer: 'ReconWriter' = None, value: 'Value' = None) -> 'OutputMessage':

        output = await OutputMessage.create('@')

        key_text = await writer.write_value(key)

        if key_text:
            await output.append(key_text)

        if value != Extant.get_extant():

            await output.append('(')

            value_text = await writer.write_value(value)
            if value.size == 0:
                return output

            if value_text:
                await output.append(value_text)

            await output.append(')')

        return output


class SlotWriter(Writer):

    @staticmethod
    async def write(key: Value = None, writer: 'ReconWriter' = None, value: 'Value' = None) -> 'OutputMessage':
        output = await OutputMessage.create()

        key_text = await writer.write_value(key)

        if key_text:
            await output.append(key_text)

        await output.append(':')

        value_text = await writer.write_value(value)

        if value_text:
            await output.append(value_text)

        return output


class StringWriter(Writer):

    @staticmethod
    async def write(value: str = None) -> 'OutputMessage':
        output = await OutputMessage.create('"')

        if value:
            await output.append(value)

        await output.append('"')

        return output


class NumberWriter(Writer):

    @staticmethod
    async def write(value: Union[int, float] = None) -> 'OutputMessage':
        output = await OutputMessage().create()

        if value:
            await output.append(value)

        return output


class BoolWriter(Writer):

    @staticmethod
    async def write(value: bool = None) -> 'OutputMessage':

        if value:
            return await OutputMessage.create('true')
        else:
            return await OutputMessage.create('false')


class IdentWriter(Writer):

    @staticmethod
    async def write(value: str = None) -> 'OutputMessage':
        output = await OutputMessage.create()

        if value:
            await output.append(value)

        return output
