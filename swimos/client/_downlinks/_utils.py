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

import inspect
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable
from swimos.structures import RecordMap, Slot, Text, RecordConverter, Attr
from swimos.structures._structs import _Item, _Record


def before_open(function: 'Callable') -> 'Callable':
    """
    Decorator that allows for a given downlink method to be executed only before the downlink has been opened.
    The downlink should have an `is_open` flag set to False.

    :param function:        - Decorated downlink method.
    :return:                - The return value of the decorated downlink method.
    """

    def wrapper(*args, **kwargs):
        if not args[0]._is_open:
            return function(*args, **kwargs)
        else:
            try:
                raise Exception(f'Cannot execute "{function.__name__}" after the downlink has been opened!')
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                args[0]._client._handle_exception(exc_value, exc_traceback)

    return wrapper


def after_open(function: 'Callable') -> 'Callable':
    """
    Decorator that allows for a given downlink method to be executed only after the downlink has been opened.
    The downlink should have an `is_open` flag set to True.

    :param function:        - Decorated downlink method.
    :return:                - The return value of the decorated downlink method.
    """

    def wrapper(*args, **kwargs):
        if args[0]._is_open:
            return function(*args, **kwargs)
        else:
            try:
                raise Exception(f'Cannot execute "{function.__name__}" before the downlink has been opened!')
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                args[0]._client._handle_exception(exc_value, exc_traceback)

    return wrapper


def convert_to_async(function: 'Any') -> 'Callable':
    """
    Convert regular function into a asynchronous function.

    :param function:        - Function to convert.
    :return:                - Converted asynchronous function.
    """

    async def async_func(*args):
        return function(*args)

    return async_func


def validate_callback(callback: 'Callable') -> 'Callable':
    """
    Validate if a callback is an asynchronous function. If it is a normal function,
    convert it to asynchronous. Otherwise, raise an exception.

    :param callback:        - Callback to validate.
    :return:                - Asynchronous callback.
    """
    if not inspect.iscoroutinefunction(callback) and isinstance(callback, Callable):
        callback = convert_to_async(callback)

    if inspect.iscoroutinefunction(callback):
        return callback
    else:
        raise TypeError('Callback must be a coroutine or a function!')


class MapRequest(ABC):

    def __init__(self, key: Any, value: Any = None) -> None:
        self.key = key
        self.value = value

    @abstractmethod
    def to_record(self):
        """
        Convert the request to a Record object.

        :return:            - Record object representing the request.
        """
        raise NotImplementedError

    def get_key_item(self) -> '_Record':
        """
        Convert the request key into an Item object.

        :return:            - Request key as an Item object.
        """
        key_slot = RecordMap.create()
        key_slot.add(
            Slot.create_slot(Text.create_from('key'), RecordConverter.get_converter().object_to_record(self.key)))

        return key_slot

    def get_value_item(self) -> '_Item':
        """
        Convert the request value into an Item object.

        :return:            - Request value as an Item object.
        """
        value_slot = RecordConverter.get_converter().object_to_record(self.value)
        return value_slot


class UpdateRequest(MapRequest):

    def to_record(self) -> '_Record':
        key_slot = self.get_key_item()
        value_slot = self.get_value_item()

        update_record = RecordMap.create_record_map(Attr.create_attr(Text.create_from('update'), key_slot))
        update_record.add(value_slot)
        return update_record


class RemoveRequest(MapRequest):
    def to_record(self) -> '_Record':
        key_slot = self.get_key_item()

        remove_record = RecordMap.create_record_map(Attr.create_attr(Text.create_from('remove'), key_slot))
        return remove_record
