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

if __name__ == '__main__':
    with SwimClient() as swim_client:
        host_uri = 'ws://localhost:9001'
        node_uri = '/unit/foo'

        for i in range(0, 10):
            swim_client.command(host_uri, node_uri, 'publish', Value.absent())
            time.sleep(5)

        print('Stopping the client in 2 seconds')
        time.sleep(2)
