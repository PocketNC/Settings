#!/usr/bin/python3

"""
This module connects the GPIO between two boards via a USB HIDRAW interface
"""

import sys
import os

sys.path.append('/opt/source/pocketnc/python')
import hal
import linuxcnc
import time
import serial

from glob import glob

#POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')
POCKETNC_VAR_DIRECTORY = '/var/opt/pocketnc/'
POCKETNC_INI_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "PocketNC.ini")

def detect_trinket():
    acms = glob('/dev/ttyA*')
    print(acms)
    for acm in acms:
        print(f"Checking {acm}...")
        s = serial.Serial(acm, baudrate=115200)
        s.readlines()
        val = str(s.read(6), 'ascii')
        s.close()
        if val.startswith('0b'):
            return acm
    return False
    

if __name__ == "__main__":
    # What shows up in halcmd show comp
    pause = 60
    hal_component = hal.component("gpio_expander")
    hal_component.setprefix("gpio_expander") # What does this do?
    in_01 = hal_component.newpin("in-0", hal.HAL_BIT, hal.HAL_OUT)
    in_01_i = hal_component.newpin("in-0.inverted", hal.HAL_BIT, hal.HAL_IN)
    in_02 = hal_component.newpin("in-1", hal.HAL_BIT, hal.HAL_OUT)
    in_02_i = hal_component.newpin("in-1.inverted", hal.HAL_BIT, hal.HAL_IN)
    out_01 = hal_component.newpin("out-0", hal.HAL_BIT, hal.HAL_IN)
    out_02 = hal_component.newpin("out-1", hal.HAL_BIT, hal.HAL_IN)
    hal_component.ready()

    ini = linuxcnc.ini(POCKETNC_INI_FILE)
    l_cmd = linuxcnc.command()
    l_status = linuxcnc.stat()

    # TODO: Have udev statically assign an event device
    #       based upon a serial number on the HID

    # These are largely arbitrary, but require that the Trinket's
    # serial interfaces are enumerated before any other. See the
    # udev comment above

    try:
        print("Listening for events")
        while True:
            try:
                acm = '/dev/ttyACM1'
            except:
                print("Serial interface disappeared")
                print("Sleeping 20 seconds before attempting again")
                time.sleep(20)
                pass
            # acm = detect_trinket()  # In future Python releases (3.8+), we can use acm := 
            # while not acm:
            #     acm = detect_trinket()
            #     time.sleep(5)
            #     print("No device...")
            # print(f"Device: {acm}")
            s = serial.Serial(acm, baudrate=115200)
            try:
                event = s.read(6)
                event = str(event, 'ascii')
                in_01.value = int(event[2])
                in_01_i.value = in_01.value ^ 1 
                in_02.value = int(event[3])
                in_02_i.value = in_02.value ^ 1
                print(event)

                new_state = 0b0000
                new_state = new_state + int(out_01.value) * 1
                new_state = new_state + int(out_02.value) * 2
                new_state = new_state + int(in_01.value) * 4
                new_state = new_state + int(in_02.value) * 8
                out_str = f"{int(new_state):#06b}"
                out_bin = bytes(out_str, 'ascii')    
                s.write(out_bin)
            except serial.SerialException:
                print("Device Disconnected")

    except KeyboardInterrupt:
        print("CTRL+C Caught")
        raise SystemExit


