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

import math
from abc import ABC, abstractmethod
from typing import Optional
from swimos.recon import Recon
from swimos.structures import Attr, Value, Num, RecordMap
from swimos.structures._structs import _Record, _Item


class _Envelope(ABC):

    def __init__(self, node_uri: str, lane_uri: str, tag: str, form: '_Form', body: _Item = Value.absent()) -> None:
        self._node_uri = node_uri
        self._lane_uri = lane_uri
        self._tag = tag
        self._form = form
        self._body = body

    @staticmethod
    def _create_from_value(value: RecordMap) -> '_Envelope':
        """
        Parse a Swim value object into an Envelope.

        :param value:           - Swim value object.
        :return:                - Envelope from the Swim value object.
        """
        tag = value._tag
        form = _Envelope._resolve_form(tag)

        return form._cast(value)

    def _to_value(self) -> Value:
        """
        Create a Swim value object representing this Envelope.

        :return:                - Swim value object from this Envelope.
        """
        return self._form._mold(self)

    @property
    def _route(self) -> str:
        return f'{self._node_uri}/{self._lane_uri}'

    @staticmethod
    def _parse_recon(recon_message: str) -> Optional['_Envelope']:
        """
        Parse a Recon message in string format into an Envelope.

        :param recon_message    - Recon message in string format.
        :return:                - Envelope from the Recon message.
        """
        value = Recon.parse(recon_message)
        if isinstance(value, RecordMap):
            return _Envelope._create_from_value(value)

    @staticmethod
    def _resolve_form(tag: str) -> '_Form':
        """
        Returns a Swim form corresponding to a given tag.

        :param tag:             - Name of the tag as string.
        :return:                - The form corresponding to the tag.
        """

        if tag == 'link':
            return _LinkRequestForm()
        if tag == 'sync':
            return _SyncRequestForm()
        if tag == 'synced':
            return _SyncedResponseForm()
        if tag == 'linked':
            return _LinkedResponseForm()
        if tag == 'unlinked':
            return _UnlinkedResponseForm()
        if tag == 'event':
            return _EventMessageForm()
        if tag == 'command':
            return _CommandMessageForm()
        else:
            raise TypeError(f'Invalid form tag: {tag}')

    def _to_recon(self) -> str:
        """
        Create a Recon message in string format representing this Envelope.

        :return:                - Recon message in string format from this Envelope.
        """
        return Recon.to_string(self._to_value())


class _LinkAddressedEnvelope(_Envelope):

    def __init__(self, node_uri: str, lane_uri: str, prio: float, rate: float, tag: str, form: '_Form',
                 body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, tag, form, body)
        self._prio = prio
        self._rate = rate


class _LaneAddressedEnvelope(_Envelope):

    def __init__(self, node_uri: str, lane_uri: str, tag: str, form: '_Form', body=Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, tag, form, body)


class _LinkRequest(_LinkAddressedEnvelope):

    def __init__(self, node_uri: str, lane_uri: str, prio: float = 0.0, rate: float = 0.0,
                 body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, prio, rate, tag='link', form=_LinkRequestForm(), body=body)


class _SyncRequest(_LinkAddressedEnvelope):

    def __init__(self, node_uri: str, lane_uri: str, prio: float = 0.0, rate: float = 0.0,
                 body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, prio, rate, tag='sync', form=_SyncRequestForm(), body=body)


class _LinkedResponse(_LinkAddressedEnvelope):

    def __init__(self, node_uri: str, lane_uri: str, prio: float = 0.0, rate: float = 0.0,
                 body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, prio, rate, tag='linked', form=_LinkedResponseForm(), body=body)


class _UnlinkedResponse(_LinkAddressedEnvelope):
    def __init__(self, node_uri: str, lane_uri: str, prio: float = 0.0, rate: float = 0.0,
                 body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, prio, rate, tag='unlinked', form=_UnlinkedResponseForm(), body=body)


class _SyncedResponse(_LaneAddressedEnvelope):

    def __init__(self, node_uri: str, lane_uri: str, body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, tag='synced', form=_SyncedResponseForm(), body=body)


class _CommandMessage(_LaneAddressedEnvelope):

    def __init__(self, node_uri: str, lane_uri: str, body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, tag='command', form=_CommandMessageForm(), body=body)


class _EventMessage(_LaneAddressedEnvelope):

    def __init__(self, node_uri: str, lane_uri: str, body: _Item = Value.absent()) -> None:
        super().__init__(node_uri, lane_uri, tag='event', form=_EventMessageForm(), body=body)


class _Form(ABC):

    @property
    @abstractmethod
    def _tag(self) -> str:
        """
        Return the tag associated with the given Form object.

        :return:                - Name of the tag as string value.
        """
        raise NotImplementedError

    @abstractmethod
    def _mold(self, envelope: '_Envelope') -> 'Value':
        """
        Create a value object from a given Envelope.

        :param envelope:        - Envelope to convert to Value object.
        :return:                - Value object representing the Envelope.
        """
        raise NotImplementedError

    @abstractmethod
    def _cast(self, item: RecordMap) -> '_Envelope':
        """
        Create an Envelope object from a RecordMap.

        :param item:            - RecordMap to convert to Envelope.
        :return:                - Envelope object created from the RecordMap.
        """
        raise NotImplementedError


class _LinkAddressedForm(_Form):

    @abstractmethod
    def _create_envelope_from(self, node_uri: str, lane_uri: str, prio: float, rate: float,
                              body: '_Item') -> '_Envelope':
        """
        Create an Envelope object corresponding to the given LinkAddressedForm.

        :param node_uri:        - Node URI of the Envelope.
        :param lane_uri:        - Lane URI of the Envelope.
        :param prio:            - Priority of the Envelope.
        :param rate:            - Rate of the Envelope.
        :param body:            - Body of the Envelope.
        :return:                - Envelope corresponding to the LinkAddressedForm.
        """
        raise NotImplementedError

    def _mold(self, envelope: Optional['_LinkAddressedEnvelope']) -> 'Value':

        if envelope is not None:

            headers = _Record.create()._add_slot('node', envelope._node_uri)._add_slot('lane', envelope._lane_uri)
            prio = envelope._prio

            if prio != 0 and not math.isnan(prio):
                headers._add_slot('prio', Num.create_from(prio))

            rate = envelope._rate

            if rate != 0 and not math.isnan(rate):
                headers._add_slot('rate', Num.create_from(rate))

            return Attr.create_attr(self._tag, headers)._concat(envelope._body)
        else:
            return _Item.extant()

    def _cast(self, value: RecordMap) -> Optional['_Envelope']:
        headers = value._get_headers(self._tag)
        node_uri = None
        lane_uri = None
        prio = 0.0
        rate = 0.0

        for index in range(0, headers.size):
            header = headers.get_item(index)
            key = header.key.get_string_value()

            if key is not None:

                if key == 'node':
                    node_uri = header.value.get_string_value()
                elif key == 'lane':
                    lane_uri = header.value.get_string_value()
                elif key == 'prio':
                    prio = header.value.get_num_value()
                elif key == 'rate':
                    rate = header.value.get_num_value()

        if node_uri is not None and lane_uri is not None:
            body = value.get_body()
            return self._create_envelope_from(node_uri, lane_uri, prio, rate, body)


class _LaneAddressedForm(_Form):

    @abstractmethod
    def _create_envelope_from(self, node_uri: str, lane_uri: str, body: _Item) -> '_Envelope':
        """
        :param node_uri:        - Node URI of the Envelope.
        :param lane_uri:        - Lane URI of the Envelope.
        :param body:            - Body of the Envelope.
        :return:                - Envelope corresponding to the LaneAddressedForm.
        """
        raise NotImplementedError

    def _mold(self, envelope: Optional['_LaneAddressedEnvelope']) -> 'Value':

        if envelope is not None:
            headers = _Record.create()._add_slot('node', envelope._node_uri)._add_slot('lane', envelope._lane_uri)
            return Attr.create_attr(self._tag, headers)._concat(envelope._body)
        else:
            return _Item.extant()

    def _cast(self, item: 'RecordMap') -> Optional['_Envelope']:
        value = item
        headers = value._get_headers(self._tag)
        node_uri = None
        lane_uri = None

        for index in range(0, headers.size):
            header = headers.get_item(index)
            key = header.key.get_string_value()

            if key is not None:

                if key == 'node':
                    node_uri = header.value.get_string_value()
                elif key == 'lane':
                    lane_uri = header.value.get_string_value()

        if node_uri is not None and lane_uri is not None:
            body = value.get_body()
            return self._create_envelope_from(node_uri, lane_uri, body)


class _SyncRequestForm(_LinkAddressedForm):

    @property
    def _tag(self) -> str:
        return 'sync'

    def _create_envelope_from(self, node_uri: str, lane_uri: str, prio: float, rate: float, body: _Item) -> '_Envelope':
        return _SyncRequest(node_uri, lane_uri, prio, rate, body=body)


class _SyncedResponseForm(_LaneAddressedForm):

    @property
    def _tag(self) -> str:
        return 'synced'

    def _create_envelope_from(self, node_uri: str, lane_uri: str, body: _Item) -> '_Envelope':
        return _SyncedResponse(node_uri, lane_uri, body=body)


class _LinkRequestForm(_LinkAddressedForm):

    @property
    def _tag(self) -> str:
        return 'link'

    def _create_envelope_from(self, node_uri: str, lane_uri: str, prio: float, rate: float, body: _Item) -> '_Envelope':
        return _LinkRequest(node_uri, lane_uri, prio, rate, body=body)


class _LinkedResponseForm(_LinkAddressedForm):

    @property
    def _tag(self) -> str:
        return 'linked'

    def _create_envelope_from(self, node_uri: str, lane_uri: str, prio: float, rate: float, body: _Item) -> '_Envelope':
        return _LinkedResponse(node_uri, lane_uri, prio, rate, body=body)


class _UnlinkedResponseForm(_LinkAddressedForm):

    @property
    def _tag(self) -> str:
        return 'unlinked'

    def _create_envelope_from(self, node_uri: str, lane_uri: str, prio: float, rate: float,
                              body: '_Item') -> '_Envelope':
        return _UnlinkedResponse(node_uri, lane_uri, prio, rate, body=body)


class _CommandMessageForm(_LaneAddressedForm):

    @property
    def _tag(self) -> str:
        return 'command'

    def _create_envelope_from(self, node_uri: str, lane_uri: str, body: _Item) -> '_Envelope':
        return _CommandMessage(node_uri, lane_uri, body=body)


class _EventMessageForm(_LaneAddressedForm):

    @property
    def _tag(self) -> str:
        return 'event'

    def _create_envelope_from(self, node_uri: str, lane_uri: str, body: _Item) -> '_Envelope':
        return _EventMessage(node_uri, lane_uri, body)
