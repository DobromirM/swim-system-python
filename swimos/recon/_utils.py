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
from typing import Optional, Union, Any


class _ReconUtils:

    @staticmethod
    def _is_ident_start_char(char: Union[str, int]) -> bool:
        """
        Check if a character is a valid first character of an identifier.
        Valid start characters for identifiers: [A-Za-z_]

        :param char:        - Character to check.
        :return:            - True if the character is valid, False otherwise.
        """
        if char:
            char = _ReconUtils._to_ord(char)

            return ord('A') <= char <= ord('Z') or char == ord('_') or ord('a') <= char <= ord('z')
        else:
            return False

    @staticmethod
    def _is_ident_char(char: Union[str, int]) -> bool:
        """
        Check if a character is a valid character of an identifier.
        Valid characters for identifiers: [A-Za-z_-]

        :param char:        - Character to check.
        :return:            - True if the character is valid, False otherwise.
        """
        if char:
            char = _ReconUtils._to_ord(char)
            return char == ord('-') or _ReconUtils._is_digit(char) or _ReconUtils._is_ident_start_char(char)
        else:
            return False

    @staticmethod
    def _is_ident(value: str) -> bool:
        """
        Check if a string value is a valid identifier.

        :param value:      - Value to check.
        :return:           - True if the value is valid identifier, False otherwise.
        """
        if len(value) == 0:
            return False

        if not _ReconUtils._is_ident_start_char(value[0]):
            return False

        for char in value:
            if not _ReconUtils._is_ident_char(char):
                return False

        return True

    @staticmethod
    def _is_space(char: Union[str, int]) -> bool:
        """
        Check if a character is a space character.

        :param char:        - Character to check.
        :return:            - True if the character is a space character, False otherwise.
        """
        if char:
            char = _ReconUtils._to_ord(char)
            return char == ord(' ') or char == ord('\t')
        else:
            return False

    @staticmethod
    def _is_digit(char: Union[str, int]) -> bool:
        """
       Check if a character is a digit.

       :param char:         - Character to check.
       :return:             - True if the character is a digit, False otherwise.
       """
        if char:
            char = _ReconUtils._to_ord(char)
            return ord('0') <= char <= ord('9')
        else:
            return False

    @staticmethod
    def _to_ord(char: Any) -> Optional[int]:
        """
        Convert a character to its integer representation.

        :param char:        - Character to convert.
        :return:            - Integer representation of the character.
        """
        if isinstance(char, str):
            return ord(char)
        if isinstance(char, int):
            return char
        else:
            return None


class _Message(ABC):

    def __init__(self) -> None:
        self._message = ''

    @property
    def _value(self) -> str:
        return self._message

    @property
    def _size(self) -> int:
        return len(self._message)

    @staticmethod
    @abstractmethod
    def _create(chars: str) -> '_Message':
        raise NotImplementedError

    def _append(self, obj: Any) -> None:
        """
        Append the string representation of an object to the current message.

        :param obj:           - Object to append to the message.
        """
        if isinstance(obj, str):
            self._message = self._message + obj
        elif isinstance(obj, (float, int)):
            self._message = self._message + str(obj)
        elif isinstance(obj, (_OutputMessage, _InputMessage)):
            self._message = self._message + obj._value
        else:
            raise TypeError(f'Item of type {type(obj).__name__} cannot be added to Message!')


class _OutputMessage(_Message):

    def __init__(self) -> None:
        super().__init__()

    @property
    def _last_char(self) -> str:
        """
        Return the last character of the message.

        :return:                - Last character of the message.
        """
        if self._size > 0:
            return self._message[-1]
        else:
            return ''

    @staticmethod
    def _create(chars: str = None) -> '_OutputMessage':
        """
        Create an OutputMessage instance and initialise its message.

        :param chars:           - Initial value of the message.
        :return:                - OutputMessage instance.
        """
        instance = _OutputMessage()

        if chars:
            instance._append(chars)

        return instance


class _InputMessage(_Message):

    def __init__(self) -> None:
        super().__init__()
        self.index = 0

    @property
    def _head(self) -> str:
        """
        Get the character at the front of the InputMessage pointed by the message index.

        :return:                - The current head character of the InputMessage.
        """
        if self._is_cont:
            return self._message[self.index]
        else:
            return ''

    @property
    def _is_cont(self) -> bool:
        """
        Check if there are any characters left in front of the InputMessage index.

        :return:                - False if the index is pointing at the last character or beyond, True otherwise.
        """
        if self.index >= len(self._message):
            return False
        else:
            return True

    @staticmethod
    def _create(chars: str = None) -> '_InputMessage':
        """
        Create an OutputMessage instance and initialise its message.

        :param chars:           - Initial value of the message.
        :return:                - OutputMessage instance.
        """
        instance = _InputMessage()

        if chars:
            instance._append(chars)

        return instance

    @staticmethod
    def _skip_spaces(message: '_InputMessage') -> None:
        """
        Moves the head of the message to the next non-space character.

        :param message:     - InputMessage object.
        """
        char = message._head
        while _ReconUtils._is_space(char):
            char = message._step()

    def _step(self) -> str:
        """
        Move the head index forward by one.

        :return:                - The new head character of the InputMessage.
        """
        self.index = self.index + 1
        return self._head
