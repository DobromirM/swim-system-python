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

import time
from swimos import SwimClient


async def custom_did_set(new_value, old_value):
    print(f'Link watched info change TO {new_value} FROM {old_value}')


if __name__ == '__main__':
    with SwimClient() as swim_client:
        host_uri = 'ws://localhost:9001'
        node_uri = '/unit/foo'

        value_downlink = swim_client.downlink_value()
        value_downlink.set_host_uri(host_uri)
        value_downlink.set_node_uri(node_uri)
        value_downlink.set_lane_uri('info')
        value_downlink.did_set(custom_did_set)
        value_downlink.open()

        # Send using either the proxy command lane...
        swim_client.command(host_uri, node_uri, 'publishInfo', 'Hello from command, world!')

        # ...or a downlink set()
        value_downlink.set('Hello from link, world!')

        time.sleep(2)
        print(f'Synchronous link get: {value_downlink.get()}')

        print('Stopping the client in 2 seconds')
        time.sleep(2)
