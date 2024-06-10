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
from swimos.structures import Value


async def custom_did_update(key, new_value, old_value):
    print(f'The lights in room {key} are {"on" if new_value else "off"}')


if __name__ == '__main__':
    with SwimClient() as swim_client:
        host_uri = 'warp://localhost:9001'
        building_uri = '/building/swim'
        first_room_uri = '/swim/1'
        second_room_uri = '/swim/2'
        third_room_uri = '/swim/3'

        map_downlink = swim_client.downlink_map()
        map_downlink.set_host_uri(host_uri)
        map_downlink.set_node_uri(building_uri)
        map_downlink.set_lane_uri('lights')
        map_downlink.did_update(custom_did_update)
        map_downlink.open()

        time.sleep(2)

        swim_client.command(host_uri, first_room_uri, "toggleLights", Value.absent())
        swim_client.command(host_uri, second_room_uri, "toggleLights", Value.absent())
        swim_client.command(host_uri, third_room_uri, "toggleLights", Value.absent())
        swim_client.command(host_uri, second_room_uri, "toggleLights", Value.absent())
        swim_client.command(host_uri, second_room_uri, "toggleLights", Value.absent())
        swim_client.command(host_uri, third_room_uri, "toggleLights", Value.absent())

        print('Stopping the client in 2 seconds')
        time.sleep(2)
