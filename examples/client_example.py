#  Copyright 2015-2019 SWIM.AI inc.
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

# Setting the value of a value lane on a remote agent.
import time

from swimos import SwimClient
from swimos.structures import Num


async def custom_on_event_callback(event):
    print(f'link received event: {event}')


with SwimClient(debug=True) as swim_client:
    host_uri = 'ws://localhost:9001'
    node_uri = '/unit/foo'
    lane_uri = 'publishValue'

    event_downlink = swim_client.downlink_event()
    event_downlink.set_host_uri('ws://localhost:9001')
    event_downlink.set_node_uri(node_uri)
    event_downlink.set_lane_uri(lane_uri)
    event_downlink.on_event(custom_on_event_callback)
    event_downlink.open()

    new_value = 'Hello from Python!'
    swim_client.command(host_uri, node_uri, "publish", Num.create_from(13))

    print('Stopping the client in 5 seconds')
    time.sleep(2)
