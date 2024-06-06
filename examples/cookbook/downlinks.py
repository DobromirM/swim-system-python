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

import random
import time
from swimos import SwimClient

if __name__ == '__main__':
    with SwimClient() as swim_client:
        host_uri = 'warp://localhost:9001'
        node_uri_prefix = '/unit/'

        map_downlink = swim_client.downlink_map()
        map_downlink.set_host_uri(host_uri)
        map_downlink.set_node_uri(node_uri_prefix + '0')
        map_downlink.set_lane_uri('shoppingCart')
        map_downlink.open()

        map_downlink.put('FromClientLink', 25)

        time.sleep(2)
        map_downlink.close()

        items = ['bat', 'cat', 'rat']

        for i in range(0, 50):
            swim_client.command(host_uri, node_uri_prefix + str(i % 3), 'addItem', items[random.randint(0, 2)])

        print('Stopping the client in 2 seconds')
        time.sleep(2)
