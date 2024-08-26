#!/usr/bin/env python3
import contextlib
import time
from math import nan
from threading import Thread, ThreadError

import btmgmt
from bluepy import btle
from bluepy.btle import BTLEDisconnectError
from lywsd03mmc import Lywsd03mmcClient
from tango import (AttrWriteType, Database, DevFailed,
                   DevState, DeviceProxy, Util)
from tango.server import attribute, command, Device, device_property, run


class SensorConnection(Lywsd03mmcClient):
    """
    A customized child class of Lywsd03mmcClient class that redefines its
    connect() and disconnect() methods using the built-in bluetooth
    controller even if a variety of USB bluetooth-controllers are
    connected to the operator's computer.
    @param controller_mac: mac address of the built-in bluetooth controller.
    """

    def __init__(self, mac, controller_mac: str):
        super().__init__(mac)

        bt_interface = {'B8:27:EB:B0:36:8F': '1', '00:1A:7D:DA:71:13': '0'}
        # bt_interface = {}
        # hci_list = []

        # parse_mac = re.compile(r'(?:[0-9a-fA-F]:?){12}')
        # parse_hci = re.compile(r'hci[0-9]+')

        # contr_mac = re.findall(parse_mac, str(response))
        # hci = re.findall(parse_hci, str(response))
        # if len(hci) > 1:
        #     hci.pop()

        # for i in range(len(hci)):
        #     hci_list.append(hci[i][-1])

        # bt_interface = dict(
        #     [(key, value) for i, (key, value) in enumerate(zip(contr_mac,
        #                                                        hci_list))]
        #     )

        self.addrType = btle.ADDR_TYPE_PUBLIC
        self.iface = bt_interface[controller_mac]

    @contextlib.contextmanager
    def connect(self):
        if self._context_depth == 0:
            self._peripheral.connect(self._mac,
                                     btle.ADDR_TYPE_PUBLIC,
                                     self.iface)
        self._context_depth += 1
        try:
            yield self
        finally:
            self._context_depth -= 1
            if self._context_depth == 0:
                self._peripheral.disconnect()

    def disconnect(self):
        self._peripheral.disconnect()


class XiaomiMijia2Host(Device):
    """
    A tango device class to serve multiple temperature sensors
    within one bluetooth controller.
    """

    controller_mac = device_property(
                                dtype=str,
                                doc="Mac-address of a bluetooth controller"
                                "used for communication with devices",
                                mandatory=True)

    RETRY_PERIOD = 120

    _db = None
    _thread = None

    device_data = {}
    device_list = []

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        self._db = Database()
        datum = self._db.get_device_name(Util.instance().get_ds_name(),
                                         "XiaomiMijia2")
        for dev_name in datum.value_string:
            self.device_list.append(self._db.get_device_property(
                                            dev_name,
                                            "mac_address")["mac_address"][0])
        self.info_stream("{}".format(self.device_list))

        for device in self.device_list:
            self.device_data[device] = [0.1, 2, 3]
        try:
            self._thread = Thread(target=self.__receive_sensor_data)
            self._thread.start()
        except ThreadError as te:
            self.error_stream("Unable to start a thread due to the"
                              "following error: {} ".format(te))
            self.set_state(DevState.FAULT)
            raise DevFailed()
        self.set_state(DevState.ON)

    @command(dtype_in=str, dtype_out=float)
    def read_temperature(self, device_mac_address: str) -> float:
        """
        A command to read temperature from updatable hash
        via device's mac address as a key.
        @param device_mac_address: mac address of a specific device.
        @return: temperature in float received from a specific device.
        """
        return self.device_data[device_mac_address][0]

    @command(dtype_in=str, dtype_out=int)
    def read_humidity(self, device_mac_address: str) -> int:
        """
        A command to read humidity from updatable hash
        via device's mac address as a key.
        @param device_mac_address: mac address of a specific device.
        @return: humidity in int received from a specific device.
        """
        return self.device_data[device_mac_address][1]

    @command(dtype_in=str, dtype_out=int)
    def read_battery(self, device_mac_address: str) -> int:
        """
        A command to read battery from updatable hash
        via device's mac address as a key.
        @param device_mac_address: mac address of a specific device.
        @return: battery in int received from a specific device.
        """
        return self.device_data[device_mac_address][2]

    def __receive_sensor_data(self):
        """
        A command to perform sequential polling of sensors in a loop
        once in a specified period of time.
        Default setting of polling is 120 seconds (RETRY_PERIOD parameter).
        Uses device mac address as a key to write its temperature, humidity
        and battery parameters as corresponding values into hash.
        The bluetooth controller can be connected to only one device at a time.
        Invokes read_temperature(), read_humidity(), read_battery() methods.
        Is called within init_device() method in a thread.
        Allowed DevState states: ON, INIT.
        """
        loop = 0
        while (self.get_state() == DevState.ON
               or self.get_state() == DevState.INIT):
            for device in self.device_list:
                try:
                    self.info_stream("Starting loop N {}".format(loop))
                    self.info_stream(
                        "Receiving data from {} device".format(device))
                    client = SensorConnection(device,
                                              self.controller_mac)
                    self.device_data[device] = [client.data.temperature,
                                                client.data.humidity,
                                                client.data.battery]
                    self.info_stream("Device {} provided the following data: "
                                     "{}, {}, {}". format(
                                        device,
                                        self.device_data[device][0],
                                        self.device_data[device][1],
                                        self.device_data[device][2]))
                    client.disconnect()
                    loop += 1
                    time.sleep(self.RETRY_PERIOD)
                except BTLEDisconnectError as be:
                    self.error_stream(
                        "Connection to the device {} has been "
                        "failed due to the error: {}".format(device, be))
                    self.device_data[device] = [nan, -1, -1]
                    # if deletion of a device from device_list is needed:
                    # self.device_list.remove(device)
                except TimeoutError as te:
                    self.error_stream(
                        "Connection to the controller `{}` has been "
                        "failed with following exception:\n {}".format(
                                                        self.controller_mac,
                                                        te))
                    self.set_state(DevState.FAULT)
                    raise DevFailed()
                except ConnectionError as ce:
                    self.error_stream(
                        "Connection to the device `{}` has been "
                        "failed with following exception:\n {}".format(device,
                                                                       ce))
                    self.set_state(DevState.FAULT)
                    raise DevFailed()
            time.sleep(self.RETRY_PERIOD)


class XiaomiMijia2(Device):
    """
    A Tango device class for Xiaomi Mijia 2 temperature and humidity sensor,
    model LYWSD03MMC.
    Questions a sensor once in a specified period of time to update
    'temperature', 'humidity' and 'battery' parameters.
    Default setting of polling is 120 seconds (RETRY_PERIOD parameter).
    """

    mac_address = device_property(dtype=str,
                                  doc="A device mac-address",
                                  mandatory=True)

    _host = None

    _temperature = 0.0

    @attribute(label="Temperature", dtype=float,
               access=AttrWriteType.READ,
               unit="C")
    def temperature(self) -> float:
        """
        An attribute "temperature" getter method.
        Allowed DevState states: ON
        :return: a temperature parameter in degrees Celsius.
        """
        state = self.get_state()
        if state == DevState.ON:
            self._temperature = self._host.read_temperature(self.mac_address)
            self.debug_stream("Obtained temperature {} from {} device".format(
                                                            self._temperature,
                                                            self.mac_address))
            return self._temperature
        else:
            self.error_stream("Unable to receive temperature from {} "
                              "device".format(self.mac_address))
            self.set_state(DevState.FAULT)
            raise DevFailed()

    _humidity = 0

    @attribute(label="Humidity", dtype=int,
               access=AttrWriteType.READ,
               unit="%")
    def humidity(self) -> int:
        """
        An attribute "humidity" getter method.
        Allowed DevState states: ON
        :return: a humidity parameter in percent.
        """
        state = self.get_state()
        if state == DevState.ON:
            self._humidity = self._host.read_humidity(self.mac_address)
            self.debug_stream("Obtained humidity {} from {} device".format(
                                                            self._humidity,
                                                            self.mac_address))
            return self._humidity
        else:
            self.error_stream("Unable to receive humidity from {} "
                              "device".format(self.mac_address))
            self.set_state(DevState.FAULT)
            raise DevFailed()

    _battery = 0

    @attribute(label="Battery", dtype=int,
               access=AttrWriteType.READ,
               unit="%")
    def battery(self):
        """
        An attribute "battery" getter method.
        Allowed DevState states: ON
        :return: a battery parameter in percent.
        """
        state = self.get_state()
        if state == DevState.ON:
            self._battery = self._host.read_battery(self.mac_address)
            self.debug_stream("Obtained battery {} from {} device".format(
                                                            self._battery,
                                                            self.mac_address))
            return self._battery
        else:
            self.error_stream("Unable to receive battery from {} "
                              "device".format(self.mac_address))
            self.set_state(DevState.FAULT)
            raise DevFailed()

    def init_device(self):
        Device.init_device(self)
        self._db = Database()
        hosts = self._db.get_device_name(Util.instance().get_ds_name(),
                                         XiaomiMijia2Host.__name__)
        if not hosts:
            self.error_stream("{} not found in this device server "
                              "instance".format(XiaomiMijia2Host.__name__))
            self.set_state(DevState.FAULT)
        self._host = DeviceProxy(hosts[0])
        self.set_state(DevState.ON)


def main():
    run({XiaomiMijia2Host.__name__: XiaomiMijia2Host,
         XiaomiMijia2.__name__: XiaomiMijia2})


if __name__ == '__main__':
    main()
