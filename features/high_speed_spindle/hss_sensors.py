#!/usr/bin/python3

import time
import hal
from i2c import I2C

# MPRLS is pressure sensor
MPRLS_I2CADDR = 0x18

# The MCP9808 has a default I2C address of 0x18, we set the address to 0x19 using the A0 address pin
MCP9808_I2CADDR = 0x19
MCP9808_REG_CONFIG = 0x01
MCP9808_REG_CONFIG_SHUTDOWN = 0x0100
MCP9808_REG_AMBIENT_TEMP = 0x05
MCP9808_REG_RESOLUTION = 0x08

#Value returned by sensor read methods if the read fails
SENSOR_READ_FAIL_VALUE = -999

# Returns pressure reading in MPa
def readPressure():
  try:
    i2c = I2C(MPRLS_I2CADDR)
    
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
    i2c = I2C(MCP9808_I2CADDR)
    
    # Begin
    result = i2c.write16(MCP9808_REG_CONFIG, 0x0)
    if result is not None:
      return SENSOR_READ_FAIL_VALUE

    # Set resolution
    i2c.write8(MCP9808_REG_RESOLUTION, 0x03)

    # Wake up
    conf_reg = None
    conf_reg = (i2c.readU16BE(MCP9808_REG_CONFIG))

    conf_wake = conf_reg & ~MCP9808_REG_CONFIG_SHUTDOWN
    i2c.write16(MCP9808_REG_CONFIG, conf_wake)
    time.sleep(0.250)
    
    # Read
    raw = (i2c.readU16BE(MCP9808_REG_AMBIENT_TEMP))
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

# outputs
TEMPERATURE_PIN = "temperature"
PRESSURE_PIN = "pressure"

if __name__ == "__main__":
  h = hal.component('hss_sensors')
  h.newpin(TEMPERATURE_PIN, hal.HAL_FLOAT, hal.HAL_OUT)
  h.newpin(PRESSURE_PIN, hal.HAL_FLOAT, hal.HAL_OUT)

  h[TEMPERATURE_PIN] = SENSOR_READ_FAIL_VALUE
  h[PRESSURE_PIN] = SENSOR_READ_FAIL_VALUE

  h.ready()

  try:
    while True:
      h[PRESSURE_PIN] = readPressure()
      h[TEMPERATURE_PIN] = readTemperature()

      time.sleep(1)

  except KeyboardInterrupt:
    raise SystemExit
