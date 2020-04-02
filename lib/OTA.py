#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

import network
import socket
import ujson
import uhashlib
import ubinascii
import gc
import pycom
import os
import machine
import ssl
import uselect as select #For ssl

class OTA():
    # The following two methods need to be implemented in a subclass for the
    # specific transport mechanism e.g. WiFi

    def __init__(self, logger, version):
        self.logger = logger
        self.version = version

    def connect(self):
        raise NotImplementedError()

    def get_data(self, req, dest_path=None, hash=False):
        raise NotImplementedError()

    # OTA methods
    def get_current_version(self):
        return self.version

    def get_update_manifest(self):
        req = "pyonair/pyonair.github.io/master/OTA/developOTA.list" #?current_ver={}".format(self.get_current_version())
        manifest_data, hash = self.get_data(req,None,True)
        self.logger.debug("Got manifest data: {}".format(manifest_data))
        manifest = ujson.loads(manifest_data)
        gc.collect()        
        return manifest

    def update(self):
        manifest = self.get_update_manifest()
        if manifest is None:
            self.logger.info("Already on the latest version")
            return False

        # Download new files and verify hashes
        for f in manifest['new'] + manifest['update']:
            # Up to 5 retries
            for _ in range(5):
                try:
                    self.get_file(f)
                    break
                except Exception as e:
                    self.logger.exception(str(e))
                    msg = "Error downloading `{}` retrying..."
                    self.logger.error(msg.format(f['URL']))
            else:
                raise Exception("Failed to download `{}`".format(f['URL']))

        # Backup old files
        # only once all files have been successfully downloaded
        for f in manifest['update']:
            self.backup_file(f)

        # Rename new files to proper name
        for f in manifest['new'] + manifest['update']:
            new_path = "{}.new".format(f['dst_path'])
            dest_path = "{}".format(f['dst_path'])

            os.rename(new_path, dest_path)

        # `Delete` files no longer required
        # This actually makes a backup of the files incase we need to roll back
        for f in manifest['delete']:
            self.delete_file(f)

        # Flash firmware
        if "firmware" in manifest:
            self.write_firmware(manifest['firmware'])

        # new version is the updated version
        self.version = manifest['version']

        return True

    def get_file(self, f):
        new_path = "{}.new".format(f['dst_path'])

        # If a .new file exists from a previously failed update delete it
        try:
            os.remove(new_path)
        except OSError:
            pass  # The file didnt exist

        # Download new file with a .new extension to not overwrite the existing
        # file until the hash is verified.
        hash = self.get_data(f['URL'], #.split("/", 3)[-1],
                             dest_path=new_path,
                             hash=True)

        # Hash mismatch
        if hash != f['hash']:
            self.logger.info(hash, f['hash'])
            msg = "Downloaded file's hash does not match expected hash"
            raise Exception(msg)

    def backup_file(self, f):
        bak_path = "{}.bak".format(f['dst_path'])
        dest_path = "{}".format(f['dst_path'])

        # Delete previous backup if it exists
        try:
            os.remove(bak_path)
        except OSError:
            pass  # There isnt a previous backup

        # Backup current file
        os.rename(dest_path, bak_path)

    def delete_file(self, f):
        bak_path = "/{}.bak_del".format(f)
        dest_path = "/{}".format(f)

        # Delete previous delete backup if it exists
        try:
            os.remove(bak_path)
        except OSError:
            pass  # There isnt a previous delete backup

        # Backup current file
        os.rename(dest_path, bak_path)

    def write_firmware(self, f):
        hash = self.get_data(f['URL'].split("/", 3)[-1],
                             hash=True,
                             firmware=True)
        # TODO: Add verification when released in future firmware


class WiFiOTA(OTA):
    def __init__(self, logger, ssid, password, server, port, version):
        logger.debug("WiFiOTA __init__")
        self.SSID = ssid
        self.password = password         
        self.server = server
        self.port = port
        OTA.__init__(self, logger, version)

    def connect(self):
        self.wlan = network.WLAN(mode=network.WLAN.STA)
        if not self.wlan.isconnected() or self.wlan.ssid() != self.SSID:

            for net in self.wlan.scan():
                self.logger.debug("Found SSID: {0} - ".format(net.ssid))
                if net.ssid == self.SSID:
                    self.wlan.connect(self.SSID, auth=(network.WLAN.WPA2,
                                                       self.password))
                    while not self.wlan.isconnected():
                        machine.idle()  # save power while waiting
                    self.logger.debug("Connected to WiFi (IP , Subnet , Gateway, DNS): {0}".format(self.wlan.ifconfig() ))
                    break
                
            else:
                raise Exception("Cannot find network '{0}'".format(self.SSID))
        else:
            # Already connected to the correct WiFi
            pass

    def _http_get(self, path, host):
        self.logger.debug("Enter : _http_get")
        req_fmt = 'GET /{} HTTP/1.0\r\nHost: {}\r\n\r\n'
        req = bytes(req_fmt.format(path, host), 'utf8')
        self.logger.debug("Req : {}".format(req))
        return req

    def get_data(self, req, dest_path=None, hash=False, firmware=False):
        h = None

        # Connect to server
        self.logger.info("Requesting: {}".format(req))        
        s = socket.socket()
        server_address = socket.getaddrinfo(self.server, 443)[0][-1]# This works for DNS -> IP
        ss = ssl.wrap_socket(s)
        self.logger.debug("Server address: {}".format(str(server_address)))
        
        try: # to connect
            ss.connect(server_address)
        except OSError as e:
            self.logger.debug("OSERROR connecting to SSL: {} ".format(str(e)))
            if str(e) == '119': # For non-Blocking sockets 119 is EINPROGRESS
                self.logger.debug("Connect to server in progress...")
            else:
                raise e

        #http://docs.micropython.org/en/v1.8.7/pyboard/library/select.html
        poller = select.poll()
        poller.register(s, select.POLLOUT | select.POLLIN)
        while True:
            res = poller.poll(1000) #Returns list of (obj, event, ...) 
            if res:
                if res[0][1] & select.POLLOUT:
                    self.logger.debug("Doing Handshake")
                    ss.do_handshake()
                    self.logger.debug("Handshake Done")
                    self.logger.debug("Request file: {}: {}:{}".format(req , self.server, self.port))
                    ss.sendall(self._http_get(req, "{}:{}".format(self.server, self.port)))
                    poller.modify(s,select.POLLIN)
                    continue
                if res[0][1] & select.POLLIN: #Data ready to read
                    #pollinresult = ss.recv(4092)
                    #print(pollinresult)
                    #data = bytearray(pollinresult) 
                    #print(data)
                    try:
                        content = bytearray()
                        fp = None
                        if dest_path is not None:
                            self.logger.debug("Writing file: {}".format(dest_path))
                            fp = open(dest_path, 'wb')

                        h = uhashlib.sha1()

                        # Get data from server
                        result = ss.recv(100)
                        self.logger.debug("Got chunk of data")

                        start_writing = False
                        while (len(result) > 0):
                            # Ignore the HTTP headers
                            if not start_writing:
                                self.logger.debug("Ignoring chunk header: {}".format(result))
                                if "\r\n\r\n" in result:
                                    start_writing = True
                                    self.logger.debug("Start writing file")
                                    result = result.decode().split("\r\n\r\n")[1].encode()

                            #if all headers are done, then write file
                            if start_writing:
                                if fp is None:
                                    self.logger.debug("Extending file in memory")
                                    content.extend(result)
                                else:
                                    self.logger.debug("Writing to file")
                                    fp.write(result)

                                if hash:
                                    self.logger.debug("Updating hash")
                                    h.update(result)
                            self.logger.debug("Getting next chunk")
                            result = ss.recv(100)
                        self.logger.debug("Close socket")
                        s.close()

                        if fp is not None:
                            self.logger.debug("Close file")
                            fp.close()


                    except Exception as e:
                        # Since only one hash operation is allowed at Once
                        # ensure we close it if there is an error
                        if h is not None:
                            h.digest()
                        raise e
                    
                    hash_val = ubinascii.hexlify(h.digest()).decode()
                    self.logger.debug("Hash is : {}".format(hash_val))

                    #if you just want the content and not a file , then dont specify a file name    
                    if dest_path is None:
                        self.logger.debug("Returning in memory data")
                        if hash:
                            return (bytes(content), hash_val)
                        else:
                            return (bytes(content), None)
                    elif hash:
                        return hash_val
                    break
            break
        # Request File while
        
        

