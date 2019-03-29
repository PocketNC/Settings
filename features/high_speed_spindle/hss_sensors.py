#!/usr/bin/python

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
# Minimum pressure in MPA below which machine will E-Stop (equals 20 PSI)
LOW_PRESSURE_CUTOFF = 0.137895

# The MCP9808 has a default I2C address of 0x18, we set the address to 0x19 using the A0 address pin
MCP9808_I2CADDR = 0x19
MCP9808_REG_CONFIG = 0x01
MCP9808_REG_CONFIG_SHUTDOWN = 0x0100
MCP9808_REG_AMBIENT_TEMP = 0x05
MCP9808_REG_RESOLUTION = 0x08
# Spindle min operating temp is 0C, lets put out cutoff at 1 to err on safe side
LOW_TEMP_CUTOFF = 1
# Spindle max operating temp is 40C, put cutoff at 39
HIGH_TEMP_CUTOFF = 39

# Reads pressure in MPa
def readPressure():
  try:
    i2c = None
    try:
      from Adafruit_GPIO.I2C import Device
      i2c = Device(MPRLS_I2CADDR, 0)
    except:
      from Adafruit_I2C import Adafruit_I2C
      i2c = Adafruit_I2C(MPRLS_I2CADDR, 1)
    
    time.sleep(0.1)
    
    # Command to take pressure reading
    i2c.writeList(0xAA, [0x0, 0x0]) 
    
    time.sleep(0.1)
    
    data = i2c.readList(0, 4)
    raw = data[1] << 16 | data[2] << 8 | data[3] 
    psi = (raw - 0x19999A) * 25
    psi /= float(0xE66666 - 0x19999A)
    mpa = psi * 0.0068947572932
    return mpa
  except:
    return -999

#Returns temperature reading in degrees Celsius
def readTemperature():
  try:
    i2c = None
    try:
      from Adafruit_GPIO.I2C import Device
      i2c = Device(MCP9808_I2CADDR, 0)
    except:
      from Adafruit_I2C import Adafruit_I2C
      i2c = Adafruit_I2C(MCP9808_I2CADDR, 1)
    
    # Begin
    i2c.write16(MCP9808_REG_CONFIG, 0x0)
  
    # Set resolution
    i2c.write8(MCP9808_REG_RESOLUTION, 0x03)
  
    # Wake up
    conf_reg = i2c.reverseByteOrder(i2c.readU16(MCP9808_REG_CONFIG))
    conf_wake = conf_reg & ~MCP9808_REG_CONFIG_SHUTDOWN
    i2c.write16(MCP9808_REG_CONFIG, conf_wake)
    time.sleep(0.250)
    
    # Read
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
    return -999

print "Initializing hss_sensors!"
h = hal.component("hss_sensors")

h.newpin("detected", hal.HAL_BIT, hal.HAL_OUT)
h['detected'] = os.system(DETECT_SCRIPT)

h.newpin("spindle_on", hal.HAL_BIT, hal.HAL_IN)

# set to true when an E Stop should occur
h.newpin("abort", hal.HAL_BIT, hal.HAL_IO)
h['abort'] = False

h.newpin("pressure", hal.HAL_FLOAT, hal.HAL_OUT)
h['pressure'] = readPressure()
h.newpin("p_abort", hal.HAL_BIT, hal.HAL_OUT)
h['p_abort'] = False

h.newpin("temperature", hal.HAL_FLOAT, hal.HAL_OUT)
h['temperature'] = readTemperature()
h.newpin("t_abort", hal.HAL_BIT, hal.HAL_OUT)
h['t_abort'] = False

h.ready()

abort = False

try:
  while True:
    if h['detected']:
      h['temperature'] = readTemperature()
      h['pressure'] = readPressure()
      abort = False
      if h['spindle_on']:
        if h['pressure'] < LOW_PRESSURE_CUTOFF:
          h['p_abort'] = True 
          abort = True    
        
        temperature = h['temperature'] 
        if temperature < LOW_TEMP_CUTOFF or temperature > HIGH_TEMP_CUTOFF:
          h['t_abort'] = True 
          abort = True
      
      h['abort'] = abort

      time.sleep(.1)
    else:
      time.sleep(10)
      h['detected'] = os.system(DETECT_SCRIPT)

except KeyboardInterrupt:
  raise SystemExit
