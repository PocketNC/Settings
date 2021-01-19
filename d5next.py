#!/usr/bin/python3

#********************************************************************
# Description:  d5next
#               This file, 'd5next.py', is a HAL component that 
#               has reads data from a D5 Next water cooler via
#               I2C.
#
# Author: John Allwine <john@pocketnc.com>
# License: GPL Version 2
#    
# Copyright (c) 2020 Pocket NC Company All rights reserved.
#
#*******************************************************************

from smbus import SMBus
import hal
import time

b = SMBus(3)
h = hal.component("d5next")

h.newpin("fan.output", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.voltage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.current", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.speed", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("fan.flags", hal.HAL_FLOAT, hal.HAL_OUT)

h.newpin("pump.output", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.voltage", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.current", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.speed", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("pump.flags", hal.HAL_FLOAT, hal.HAL_OUT)

h.newpin("flow", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("temperature_c", hal.HAL_FLOAT, hal.HAL_OUT)
h.newpin("temperature_f", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()

crc_table = [0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0]
def docrc16(data, crc):
  data = (data ^ (crc & 0xff)) & 0xff
  crc >>= 8
  if (crc_table[data & 0xf] ^ crc_table[data >> 4]) > 0:
    crc ^= 0xc001

  data <<= 6
  crc ^= data
  data <<= 1
  crc ^= data
  return crc

def crc16(data):
  crc = 0xffff
  for d in data:
    crc = docrc16(d, crc)
  crc ^= 0xffff
  return crc

try:
  while True:
    try:
      data = b.read_i2c_block_data(0x1e, 0x00)

      crc = ((data[23] << 8) | data[24])
      if crc == crc16(data[0:23]):
        h['fan.output'] = ((data[1] << 8) | data[2])/100    # in percentage
        h['fan.voltage'] = ((data[3] << 8) | data[4])/100   # in volts
        h['fan.current'] = ((data[5] << 8) | data[6])/1000  # in amps
        h['fan.speed'] = ((data[7] << 8) | data[8])         # in RPM
        h['fan.flags'] = data[9]

        h['pump.output'] = ((data[10] << 8) | data[11])/100    # in percentage
        h['pump.voltage'] = ((data[12] << 8) | data[13])/100   # in volts
        h['pump.current'] = ((data[14] << 8) | data[15])/1000  # in amps
        h['pump.speed'] = ((data[16] << 8) | data[17])         # in RPM
        h['pump.flags'] = data[18]

        h['flow'] = ((data[19] << 8) | data[20])/10          # in liters / hour
        h['temperature_c'] = ((data[21] << 8) | data[22])/100  # in degrees C
        h['temperature_f'] = ((data[21] << 8) | data[22])/100*9./5+32  # in degrees F

    except:
      pass

    time.sleep(1)
except KeyboardInterrupt:
  raise SystemExit


