from mqtt import MQTTClient
from network import WLAN
import machine
import time
import keys as k


def sub_cb(topic, msg):
   print(msg)


print("Trying to connect to WIFI")
wlan = WLAN(mode=WLAN.STA)
wlan.connect(k.WIFI_SSID, auth=(WLAN.WPA2, k.WIFI_PASSWORD), timeout=5000)

while not wlan.isconnected():
    machine.idle()
print("Connected to WiFi\n")

client = MQTTClient(
    k.MQTT_DEVICE_ID,
    "http://airqualitybroker.azure-devices.net",
    user="http://airqualitybroker.azure-devices.net/" + k.MQTT_DEVICE_ID + "/?api-version=2018-06-30",
    password=k.MQTT_PRIMARY_KEY,
    port=8883
)

client.set_callback(sub_cb)
print("Trying to connect to the MQTT")
client.connect()
print("Connected")

print("Subscribing to a topic")
client.subscribe(topic="youraccount/feeds/lights")

while True:
    print("Sending ON")
    client.publish(topic="youraccount/feeds/lights", msg="ON")
    time.sleep(1)
    print("Sending OFF")
    client.publish(topic="youraccount/feeds/lights", msg="OFF")
    client.check_msg()

    time.sleep(1)