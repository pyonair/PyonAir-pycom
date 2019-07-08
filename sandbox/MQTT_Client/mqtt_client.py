# Python 3.7
import time
import ttn
import struct
import base64

import sys
sys.path.append('../..')
from keys import app_id, access_key


def uplink_callback(msg, client):
    payload = msg.payload_raw
    print("Received uplink from ", msg.dev_id)
    print("msg:", msg)
    print("raw payload:", payload)
    # print("encoded payload:", int(base64.b64decode(msg.payload_raw).hex()))
    print("decoded payload:", struct.unpack('iBB', base64.b64decode(payload)))
    print()


handler = ttn.HandlerClient(app_id, access_key)
print("HandlerClient created")

# using mqtt client
mqtt_client = handler.data()
mqtt_client.set_uplink_callback(uplink_callback)
mqtt_client.connect()
print("Going to sleep")
time.sleep(20*60)
print("Closing the connection")
mqtt_client.close()
