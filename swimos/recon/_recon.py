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

from swimos.structures._structs import Value
from ._parsers import _ReconParser
from ._writers import _ReconWriter


class Recon:
    # Singletons
    _writer = None
    _parser = None

    @staticmethod
    def parse(recon_string: str) -> 'Value':
        """
        Parse a Recon message in string format and return a Swim structure object.

        :param recon_string:        - Recon message in string format.
        :return:                    - Swim structure object representing the Recon message.
        """
        return Recon._get_parser()._parse_block_string(recon_string)

    @staticmethod
    def to_string(item: 'Value') -> str:
        """
        Parse a Swim structure object to a Recon string.

        :param item:               - Swim structure object.
        :return:                   - Recon message in string format representing the Swim structure object.
        """
        return Recon._get_writer()._write_item(item)

    @staticmethod
    def _get_writer() -> '_ReconWriter':
        """
        Get a Recon writer if one already exists.
        Otherwise, instantiate a new one.

        :return:        - Recon writer.
        """
        if Recon._writer is None:
            Recon._writer = _ReconWriter()

        return Recon._writer

    @staticmethod
    def _get_parser() -> '_ReconParser':
        """
        Get a Recon parser if one already exists.
        Otherwise, instantiate a new one.

        :return:        - Recon parser.
        """
        if Recon._parser is None:
            Recon._parser = _ReconParser()

        return Recon._parser
