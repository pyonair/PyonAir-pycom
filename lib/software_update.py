from Configuration import config
from helper import wifi_lock, led_lock
import machine
import pycom
import time
from network import WLAN
from OTA import WiFiOTA


def software_update(logger):
    """
    Connects to the wlan and fetches updates from a server. After having applied the patches successfully, it reboots
    the device.
    :param logger: status logger
    :type logger: LoggerFactory object
    """

    with wifi_lock:
        try:
            logger.info("Over the Air update started")

            led_lock.acquire(1)  # disable all other indicator LEDs
            pycom.rgbled(0x555500)  # Yellow LED

            # Get credentials from configuration
            ssid = config.get_config("SSID")
            password = config.get_config("wifi_password")
            server_ip = config.get_config("server")
            port =  int(config.get_config("port"))

            logger.info("SSID: " + str(ssid))
            logger.info("server_ip: " + str(server_ip))
            logger.info("port: " + str(port))

            version = config.get_config("code_version")

            # Perform OTA update
            ota = WiFiOTA(logger, ssid, password, server_ip, port, version)

            # Turn off WiFi to save power
            w = WLAN()
            w.deinit()

            logger.info("connecting...")
            ota.connect()
            if ota.update():
                new_version = str(ota.get_current_version())  # get updated version
                config.save_config({"code_version": str(new_version)})  # save new version to config on SD
                logger.info(
                    "Successfully updated the device from version {} to version {}".format(version, new_version))

        except Exception as e:
            logger.exception("Failed to update the device")
            pycom.rgbled(0x550000)  # turn LED to RED
            time.sleep(3)

        finally:
            # Turn off update mode
            config.save_config({"update": False})

            # Turn off indicator LED
            pycom.rgbled(0x000000)
            led_lock.release()

            # Reboot the device to apply patches
            logger.info("rebooting...")
            machine.reset()
