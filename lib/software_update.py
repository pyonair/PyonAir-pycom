from Configuration import config
from helper import wifi_lock, led_lock
import machine
import pycom
import time
from network import WLAN
from OTA import WiFiOTA


def software_update(logger):

    with wifi_lock:
        try:
            logger.info("Over the Air update started")

            led_lock.acquire(1)  # disable all other indicator LEDs
            pycom.rgbled(0x555500)  # Yellow LED

            # Get credentials from configuration
            ssid = config.get_config("SSID")
            password = config.get_config("wifi_password")
            server_ip = config.get_config("server")
            port = int(config.get_config("port"))

            print(ssid, password, server_ip, port)

            # Perform OTA update
            ota = WiFiOTA(ssid, password, server_ip, port)

            # Turn off WiFi to save power
            w = WLAN()
            w.deinit()

            ota.connect()
            ota.update()

            time.sleep(5)

        except Exception as e:
            logger.exception("Failed to update the device")
            pycom.rgbled(0x550000)
            time.sleep(3)

        finally:
            # Turn off update mode
            config.save_configuration({"update": False})

            pycom.rgbled(0x000000)
            led_lock.release()

            # Reboot the device to apply patches
            machine.reset()
