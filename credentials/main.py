import network
from network import WLAN
import usocket as socket
import pycom
import gc
from machine import SD
import os

# set up pycom as access point
wlan = network.WLAN(mode=WLAN.AP, ssid='MVP')
# Connect to MVP using the passowrd pmsensor
wlan.init(mode=WLAN.AP, ssid='MVP', auth=(WLAN.WPA2, 'pmsensor'), channel=1, antenna=WLAN.INT_ANT)
# Load HTML via entering 192,168.4.10 to your browser
wlan.ifconfig(id=1, config=('192.168.4.10', '255.255.255.0', '192.168.4.1', '192.168.4.1'))


print('Access point turned on as MVP')
print('Configuration website can be accessed at 192.168.4.10')

address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]  # Accept stations from all addresses
sct = socket.socket()  # Create socket for communication
sct.settimeout(30)  # session times out after x seconds
gc.collect()  # frees up unused memory if there was a previous connection
sct.bind(address)  # Bind address to socket
sct.listen(1)  # Allow one station to connect to socket

pycom.heartbeat(False)
pycom.rgbled(0x0000FF)  # Blue LED - Initialized, waiting for connection

sd = SD()  # set up sd card
os.mount(sd, '/sd')

html_form = '''<!DOCTYPE html>
            <html>
                <head>
                    <title>Configuration</title>
                </head>
                <style>
                    body { background-color: #4CAF50; }
                    h1 { color: white; }
                    h2 { color: white; }
                    form { color: white; }
                </style>
                <body>
                    <h1>PM Sensor Configuration</h1>
                    <br>
                    <h2>Enter Credentials:</h2>
                    <p>
                    <form action="" method="post">
                            LoRa Application Key:<br>
                            <input type="text" name="APP_KEY" size="50" required>
                            <br><br>
                            LoRa Application EUI:<br>
                            <input type="text" name="APP_EUI" size="50" required>
                            <br><br>
                            Wifi Application ID:<br>
                            <input type="text" name="app_id" size="50" required>
                            <br><br>
                            Wifi Access Key:<br>
                            <input type="text" name="access_key" size="50" required>
                            <br><br>
                            <input type="submit" value="Send Credentials">
                    </form></p>
                </body>
            </html>'''


def response(APP_KEY, APP_EUI, app_id, access_key):
    html_acknowledgement = '''<!DOCTYPE html>
                <html>
                    <head>
                        <title>Configuration</title>
                    </head>
                    <style>
                        body { background-color: #4CAF50; }
                        h2 { color: white; }
                        p { color: white; }
                    </style>
                    <body>
                        <br>
                        <h2>Sensor Configured as Follows:</h2>
                        <p>LoRa Application Key:<br>'''+ APP_KEY +'''<br>
                        <br>
                        LoRa Application EUI:<br>'''+ APP_EUI +'''<br>
                        <br>
                        Wifi Application ID:<br>'''+ app_id +'''<br>
                        <br>
                        Wifi Access Key:<br>'''+ access_key +'''
                        </p>
                    </body>
                </html>'''
    return html_acknowledgement


def get_credentials():

    index = ['NaN'] * 5
    credentials = {0:'APP_KEY', 1:'APP_EUI', 2:'app_id', 3:'access_key'}

    try:
        while True:
            # print('Waiting for new connection')
            client, address = sct.accept()
            # print('Client connected at: ', address)
            client.send(html_form)  # send html page with form to submit by the user
            pycom.rgbled(0x00FF00)  # Green LED - Connection successful
            received_data = str(client.recv(3000))  # wait for client response
            for i in range(0, 4):  # find indices in received message
                index[i] = received_data.rfind(credentials[i])
            if -1 not in index[0:4]:  # if all keys were found in the message, cut them up to strings
                APP_KEY = received_data[(index[0]+8):index[1]-1]
                print("APP_KEY:", APP_KEY)
                APP_EUI = received_data[(index[1]+8):index[2]-1]
                print("APP_EUI:", APP_EUI)
                app_id = received_data[(index[2]+7):index[3]-1]
                print("app_id:", app_id)
                index[4] = received_data.find("\r", index[3])
                if index[4] != -1: # last key is not in the end of the message
                    access_key = received_data[(index[3]+11):index[4]]
                    print("access_key:", access_key)
                else: # last key is in the end of the message
                    access_key = received_data[(index[3]+11):-1]
                    print("access_key:", access_key)
                client.send(response(APP_KEY, APP_EUI, app_id, access_key))  # sends acknowledgement to user
                client.close()
                print('Credentials received')
                with open('/sd/config.txt', 'w') as f:  # save credentials to sd card
                    f.write(APP_KEY + '\r\n' + APP_EUI + '\r\n' + app_id + '\r\n' + access_key + '\r\n')
                print('Credentials saved')
                return

    except:
        pycom.rgbled(0xFF0000)  # Red LED - Connection timeout
        print('Session timed out')
        return


get_credentials()

wlan.deinit()  # turn off wifi
pycom.heartbeat(True)  # disable indicator LEDs
gc.collect()
