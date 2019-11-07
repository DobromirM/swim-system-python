from typing import Optional, Union, Any


class ReconUtils:

    @staticmethod
    async def is_ident_start_char(char: Union[str, int]) -> bool:
        """
        Check if a character is a valid first character of an identifier.
        Valid start characters for identifiers: [A-Za-z_]

        :param char:        - Character to check.
        :return:            - True if the character is valid, False otherwise.
        """
        if char:
            char = await ReconUtils.to_ord(char)

            return ord('A') <= char <= ord('Z') or char == ord('_') or ord('a') <= char <= ord('z')
        else:
            return False

    @staticmethod
    async def is_ident_char(char: Union[str, int]) -> bool:
        """
        Check if a character is a valid character of an identifier.
        Valid characters for identifiers: [A-Za-z_-]

        :param char:        - Character to check.
        :return:            - True if the character is valid, False otherwise.
        """
        if char:
            char = await ReconUtils.to_ord(char)
            return char == ord('-') or await ReconUtils.is_digit(char) or await ReconUtils.is_ident_start_char(char)
        else:
            return False

    @staticmethod
    async def is_ident(value: str) -> bool:
        """
        Check if a string value is a valid identifier.

        :param value:      - Value to check.
        :return:           - True if the value is valid identifier, False otherwise.
        """
        if len(value) == 0:
            return False

        if not await ReconUtils.is_ident_start_char(value[0]):
            return False

        for char in value:
            if not await ReconUtils.is_ident_char(char):
                return False

        return True

    @staticmethod
    async def is_space(char: Union[str, int]) -> bool:
        """
        Check if a character is a space character.

        :param char:        - Character to check.
        :return:            - True if the character is a space character, False otherwise.
        """
        if char:
            char = await ReconUtils.to_ord(char)
            return char == ord(' ') or char == ord('\t')
        else:
            return False

    @staticmethod
    async def is_digit(char: Union[str, int]) -> bool:
        """
       Check if a character is a digit.

       :param char:         - Character to check.
       :return:             - True if the character is a digit, False otherwise.
       """
        if char:
            char = await ReconUtils.to_ord(char)
            return ord('0') <= char <= ord('9')
        else:
            return False

    @staticmethod
    async def to_ord(char: Any) -> Optional[int]:
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


class OutputMessage:

    def __init__(self) -> None:
        self.message = ''

    @property
    def value(self) -> str:
        return self.message

    @property
    def size(self) -> int:
        return len(self.message)

    @property
    def last_char(self) -> str:
        if self.size > 0:
            return self.message[-1]
        else:
            return ''

    @staticmethod
    async def create(chars: str = None) -> 'OutputMessage':
        """
        Create an OutputMessage instance and initialise its message.

        :param chars:           - Initial value of the message.
        :return:                - OutputMessage instance.
        """
        instance = OutputMessage()

        if chars:
            await instance.append(chars)

        return instance

    async def append(self, obj: Any) -> None:
        """
        Append the string representation of an object to the current message.

        :param obj:           - Object to append to the message.
        """
        if isinstance(obj, str):
            self.message = self.message + obj
        elif isinstance(obj, (float, int)):
            self.message = self.message + str(obj)
        elif isinstance(obj, OutputMessage):
            self.message = self.message + obj.value
        else:
            raise TypeError(f'Item of type {type(obj).__name__} cannot be added to the OutputMessage!')


class InputMessage:

    def __init__(self, message: str) -> None:
        self.message = message
        self.index = 0

    def head(self) -> str:
        """
        Get the character at the front of the InputMessage pointed by the message index.

        :return:                - The current head character of the InputMessage.
        """
        if self.is_cont():
            return self.message[self.index]
        else:
            return ''

    def step(self) -> str:
        """
        Move the head index forward by one.

        :return:                - The new head character of the InputMessage.
        """
        self.index = self.index + 1
        return self.head()

    def is_cont(self) -> bool:
        """
        Check if there are any characters left in front of the InputMessage index.

        :return:                - False if the index is pointing at the last character or beyond, True otherwise.
        """
        if self.index >= len(self.message):
            return False
        else:
            return True
