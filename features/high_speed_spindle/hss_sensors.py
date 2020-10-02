#!/usr/bin/python3

import hal
import os
import datetime
import time

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"
DETECT_SCRIPT = os.path.join(POCKETNC_DIRECTORY, "Settings/features/high_speed_spindle/detect_hss_mprls.py")

# MPRLS is pressure sensor
MPRLS_I2CADDR = 0x18
# Upper end of the sensors scale in MPA (25 PSI)
MPRLS_SCALE_MAX = 0.172369
# Minimum pressure in MPA below which machine will E-Stop (equals 16 PSI)
LOW_PRESSURE_CUTOFF = 0.110316

# The MCP9808 has a default I2C address of 0x18, we set the address to 0x19 using the A0 address pin
MCP9808_I2CADDR = 0x19
MCP9808_REG_CONFIG = 0x01
MCP9808_REG_CONFIG_SHUTDOWN = 0x0100
MCP9808_REG_AMBIENT_TEMP = 0x05
MCP9808_REG_RESOLUTION = 0x08
# Spindle min operating temp is 0C, lets put out cutoff at 1 to err on safe side
LOW_TEMP_CUTOFF = 1
# Spindle max operating temp is 40C, put cutoff at 39
# Update: after some testing, have decided to move it to 48C.
HIGH_TEMP_CUTOFF = 48

#Value returned by sensor read methods if the read fails
SENSOR_READ_FAIL_VALUE = -999

# Returns pressure reading in MPa
def readPressure():
  try:
    i2c = None
    try:
      from Adafruit_GPIO.I2C import Device
      i2c = Device(MPRLS_I2CADDR, 2)
    except:
      from Adafruit_I2C import Adafruit_I2C
      i2c = Adafruit_I2C(MPRLS_I2CADDR, 1)
    
    time.sleep(0.1)
    
    # Command to take pressure reading
    result = i2c.writeList(0xAA, [0x0, 0x0]) 
    if result is not None:
      return SENSOR_READ_FAIL_VALUE 
    
    time.sleep(0.1)
    
    data = i2c.readList(0, 4)
    raw = data[1] << 16 | data[2] << 8 | data[3] 
    psi = (raw - 0x19999A) * 25
    psi /= float(0xE66666 - 0x19999A)
    mpa = psi * 0.0068947572932
    return mpa
  except:
    return SENSOR_READ_FAIL_VALUE

# Returns temperature reading in degrees Celsius
def readTemperature():
  try:
    i2c = None
    try:
      from Adafruit_GPIO.I2C import Device
      i2c = Device(MCP9808_I2CADDR, 2)
    except:
      from Adafruit_I2C import Adafruit_I2C
      i2c = Adafruit_I2C(MCP9808_I2CADDR, 1)
    
    # Begin
    result = i2c.write16(MCP9808_REG_CONFIG, 0x0)
    if result is not None:
      return SENSOR_READ_FAIL_VALUE

    # Set resolution
    i2c.write8(MCP9808_REG_RESOLUTION, 0x03)

    # Wake up
    conf_reg = None
    try:
      conf_reg = (i2c.readU16BE(MCP9808_REG_CONFIG))
    except:
      conf_reg = i2c.reverseByteOrder(i2c.readU16(MCP9808_REG_CONFIG))

    conf_wake = conf_reg & ~MCP9808_REG_CONFIG_SHUTDOWN
    i2c.write16(MCP9808_REG_CONFIG, conf_wake)
    time.sleep(0.250)
    
    # Read
    raw = None
    try:
      raw = (i2c.readU16BE(MCP9808_REG_AMBIENT_TEMP))
    except:
      raw = i2c.reverseByteOrder(i2c.readU16(MCP9808_REG_AMBIENT_TEMP))
    temp = raw & 0x0FFF
    temp /= 16.0
    if (raw & 0x1000):
        temp -= 256
    
    time.sleep(0.250)
    # Shutdown
    conf_shutdown = i2c.readU16(MCP9808_REG_CONFIG) | MCP9808_REG_CONFIG_SHUTDOWN
    i2c.write16(MCP9808_REG_CONFIG, conf_shutdown)
    return temp
  except:
    return SENSOR_READ_FAIL_VALUE

print "Initializing hss_sensors!"
h = hal.component("hss_sensors")

h.newpin("spindle_on", hal.HAL_BIT, hal.HAL_IN)

# set to true when an E Stop should occur
h.newpin("abort", hal.HAL_BIT, hal.HAL_OUT)
h['abort'] = False

h.newpin('pressure', hal.HAL_FLOAT, hal.HAL_OUT)
h['pressure'] = readPressure()
h.newpin('p_detected', hal.HAL_BIT, hal.HAL_OUT)
h['p_detected'] = (h['pressure'] != SENSOR_READ_FAIL_VALUE)
h.newpin('temperature', hal.HAL_FLOAT, hal.HAL_OUT)
h['temperature'] = readTemperature()
h.newpin('t_detected', hal.HAL_BIT, hal.HAL_OUT)
h['t_detected'] = (h['temperature'] != SENSOR_READ_FAIL_VALUE)

# set to true if aborting due to low pressure
h.newpin('p_abort', hal.HAL_BIT, hal.HAL_OUT)
h['p_abort'] = False
# set to true if aborting because the pressure sensor is not detected
h.newpin('p_detect_abort', hal.HAL_BIT, hal.HAL_OUT)
h['p_detect_abort'] = False
# set to true if aborting due to temperature reading outside bounds
h.newpin('t_abort', hal.HAL_BIT, hal.HAL_OUT)
h['t_abort'] = False
# set to true if aborting because the temperature sensor is not detected
h.newpin('t_detect_abort', hal.HAL_BIT, hal.HAL_OUT)
h['t_detect_abort'] = False

h.ready()

abort = False


try:
  while True:
    h['pressure'] = readPressure()
    h['p_detected'] = (h['pressure'] != SENSOR_READ_FAIL_VALUE)
    h['temperature'] = readTemperature()
    h['t_detected'] = (h['temperature'] != SENSOR_READ_FAIL_VALUE)
    abort = False
    if h['spindle_on']:
      if not h['p_detected']:
        h['p_detect_abort'] = True
        abort = True
      elif h['pressure'] < LOW_PRESSURE_CUTOFF:
        h['p_abort'] = True 
        abort = True    
      
      if not h['t_detected']:
        h['t_detect_abort'] = True
        abort = True
      elif h['temperature']  < LOW_TEMP_CUTOFF or h['temperature']  > HIGH_TEMP_CUTOFF:
        h['t_abort'] = True 
        abort = True
    
    h['abort'] = abort

    time.sleep(1)

except KeyboardInterrupt:
  raise SystemExit
