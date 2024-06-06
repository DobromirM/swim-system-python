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


async def custom_did_update(key, new_value, old_value):
    print(f'Link watched {key} changed to {new_value} from {old_value}')


if __name__ == '__main__':
    with SwimClient() as swim_client:
        host_uri = 'warp://localhost:9001'
        node_uri = '/unit/foo'

        map_downlink = swim_client.downlink_map()
        map_downlink.set_host_uri(host_uri)
        map_downlink.set_node_uri(node_uri)
        map_downlink.set_lane_uri('shoppingCart')
        map_downlink.did_update(custom_did_update)
        map_downlink.open()

        swim_client.command(host_uri, node_uri, 'addItem', 'FromClientCommand')
        map_downlink.put('FromClientLink', 25)

        time.sleep(2)
        map_downlink.remove('FromClientLink')

        print('Stopping the client in 2 seconds')
        time.sleep(2)
