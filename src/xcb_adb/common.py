# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Common code for ADB and Fastboot.

Common usb browsing, and usb communication.
"""
import logging
import platform
import socket
import threading
import weakref
import select

import serial

from xcb_adb import usb_exceptions

DEFAULT_TIMEOUT_MS = 10000

_LOG = logging.getLogger('android_usb')


def GetInterface(setting):
    """Get the class, subclass, and protocol for the given USB setting."""
    return (setting.getClass(), setting.getSubClass(), setting.getProtocol())


def InterfaceMatcher(clazz, subclass, protocol):
    """Returns a matcher that returns the setting with the given interface."""
    interface = (clazz, subclass, protocol)

    def Matcher(device):
        for setting in device.iterSettings():
            if GetInterface(setting) == interface:
                return setting

    return Matcher


class SerialHandle(object):
    def __init__(self, serial, timeout_ms=None):

        if isinstance(serial, (bytes, bytearray)):
            serial = serial.decode('utf-8')

        if ',' in serial:
            self.port, self.speed = serial.split(',')
        else:
            self.port = serial
            self.speed = 115200

        self._connection = None
        self._serial_number = '%s,%s' % (self.port, self.speed)
        self._timeout_ms = float(timeout_ms) if timeout_ms else None

        self._connect()

    def _connect(self):
        timeout = self.TimeoutSeconds(self._timeout_ms)
        
        self._connection = serial.Serial(self.port, self.speed, timeout=timeout)

    @property
    def serial_number(self):
        return self._serial_number

    def BulkWrite(self, data, timeout=None):
        t = self.TimeoutSeconds(timeout)
        _, writeable, _ = select.select([], [self._connection], [], t)
        if writeable:
            return self._connection.write(data)
        msg = 'Sending data to {} timed out after {}s. No data was sent.'.format(
            self.serial_number, t)
        raise serial.SerialTimeoutException(msg)

    def BulkRead(self, numbytes, timeout=None):
        t = self.TimeoutSeconds(timeout)
        readable, _, _ = select.select([self._connection], [], [], t)
        if readable:
            return self._connection.read(numbytes)
        msg = 'Reading from {} timed out (Timeout {}s)'.format(
            self._serial_number, t)
        #raise serial.TcpTimeoutException(msg)

    def Timeout(self, timeout_ms):
        return float(timeout_ms) if timeout_ms is not None else self._timeout_ms

    def TimeoutSeconds(self, timeout_ms):
        timeout = self.Timeout(timeout_ms)
        return timeout / 1000.0 if timeout is not None else timeout

    def Close(self):
        return self._connection.close()

class TcpHandle(object):
    """TCP connection object.

       Provides same interface as UsbHandle. """

    def __init__(self, serial, timeout_ms=None):
        """Initialize the TCP Handle.
        Arguments:
          serial: Android device serial of the form host or host:port.

        Host may be an IP address or a host name.
        """
        # if necessary, convert serial to a unicode string
        if isinstance(serial, (bytes, bytearray)):
            serial = serial.decode('utf-8')

        if ':' in serial:
            self.host, self.port = serial.split(':')
        else:
            self.host = serial
            self.port = "5555"

        self._connection = None
        self._serial_number = '%s:%s' % (self.host, self.port)
        self._timeout_ms = float(timeout_ms) if timeout_ms else None

        self._connect()

    def _connect(self):
        timeout = self.TimeoutSeconds(self._timeout_ms)
        
        self._connection = socket.create_connection((self.host, self.port),
                                                    timeout=timeout)
        if timeout:
            self._connection.setblocking(0)

    @property
    def serial_number(self):
        return self._serial_number

    def BulkWrite(self, data, timeout=None):
        t = self.TimeoutSeconds(timeout)
        _, writeable, _ = select.select([], [self._connection], [], t)
        if writeable:
            return self._connection.send(data)
        msg = 'Sending data to {} timed out after {}s. No data was sent.'.format(
            self.serial_number, t)
        raise usb_exceptions.TcpTimeoutException(msg)

    def BulkRead(self, numbytes, timeout=None):
        t = self.TimeoutSeconds(timeout)
        readable, _, _ = select.select([self._connection], [], [], t)
        if readable:
            return self._connection.recv(numbytes)
        msg = 'Reading from {} timed out (Timeout {}s)'.format(
            self._serial_number, t)
        raise usb_exceptions.TcpTimeoutException(msg)

    def Timeout(self, timeout_ms):
        return float(timeout_ms) if timeout_ms is not None else self._timeout_ms

    def TimeoutSeconds(self, timeout_ms):
        timeout = self.Timeout(timeout_ms)
        return timeout / 1000.0 if timeout is not None else timeout

    def Close(self):
        return self._connection.close()
