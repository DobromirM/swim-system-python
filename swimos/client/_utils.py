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

import sys
from typing import Callable, Optional, Tuple
from urllib.parse import urlparse, ParseResult


def after_started(function: 'Callable') -> 'Callable':
    """
    Decorator that allows for a given client method to be executed only after the client has been started.
    The client should have an `has_started` flag set to True.

    :param function:        - Decorated client method.
    :return:                - The return value of the decorated client method.
    """

    def wrapper(*args, **kwargs):
        if args[0]._has_started:
            return function(*args, **kwargs)
        else:
            try:
                raise Exception(f'Cannot execute "{args[1].__name__}" before the client has been started!')
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                args[0]._handle_exception(exc_value, exc_traceback)

    return wrapper


class _URI:

    @staticmethod
    def _parse_uri(uri: str) -> Tuple[str, str]:
        """
        Parse the given URI.

        :param uri:             - URI to parse.
        :return:                - ParseResult containing the different parts of the URI.
        """
        uri = urlparse(uri)
        normalised_scheme = _URI._normalise_scheme(uri)

        if normalised_scheme is not None:
            uri = uri._replace(scheme=normalised_scheme)
            return uri.geturl(), uri.scheme
        else:
            raise TypeError(f'Invalid scheme "{uri.scheme}" for Warp URI!')

    @staticmethod
    def _normalise_scheme(uri: ParseResult) -> Optional[str]:
        """
        Normalise all different representations of the WARP scheme to a websocket connection.

        :param uri:             - URI to normalise.
        :return:                - The corresponding scheme if the given URI is WARP compatible.
                                  None otherwise.
        """
        scheme = uri.scheme

        if scheme == 'ws' or scheme == 'warp':
            return 'ws'
        elif scheme == 'wss' or scheme == 'warps':
            return 'wss'
        else:
            return None
