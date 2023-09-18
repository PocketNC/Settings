from smbus import SMBus
import sys

class D5NextError(Exception):
  pass

class D5NextCommunicationError(D5NextError):
  pass

class D5NextInvalidDataError(D5NextError):
  pass

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

class D5Next:
  def __init__(self, address=0x1e):
    self.b = SMBus(3)
    self.address = address

  def readData(self):
    try:
      data = self.b.read_i2c_block_data(self.address, 0x00)
    except:
      raise D5NextCommunicationError("Error reading from address %s" % (self.address,))

    crc = ((data[23] << 8) | data[24])
    if crc == crc16(data[0:23]):
      self.fan_output = ((data[1] << 8) | data[2])/100    # in percentage
      self.fan_voltage = ((data[3] << 8) | data[4])/100   # in volts
      self.fan_current = ((data[5] << 8) | data[6])/1000  # in amps
      self.fan_speed = ((data[7] << 8) | data[8])         # in RPM
      self.fan_flags = data[9]

      self.pump_output = ((data[10] << 8) | data[11])/100    # in percentage
      self.pump_voltage = ((data[12] << 8) | data[13])/100   # in volts
      self.pump_current = ((data[14] << 8) | data[15])/1000  # in amps
      self.pump_speed = ((data[16] << 8) | data[17])         # in RPM
      self.pump_flags = data[18]

      self.flow = ((data[19] << 8) | data[20])/10          # in liters / hour
      self.temperature_c = ((data[21] << 8) | data[22])/100  # in degrees C
      self.temperature_f = ((data[21] << 8) | data[22])/100*9./5+32  # in degrees F
    else:
      raise D5NextInvalidDataError("Invalid CRC16 checksum")

  def getDataAsObject(self):
    return {
     "fan_output": self.fan_output,
     "fan_voltage": self.fan_voltage,
     "fan_current": self.fan_current,
     "fan_speed": self.fan_speed,
     "fan_flags": self.fan_flags,

     "pump_output": self.pump_output,
     "pump_voltage": self.pump_voltage,
     "pump_current": self.pump_current,
     "pump_speed": self.pump_speed,
     "pump_flags": self.pump_flags,

     "flow": self.flow,
     "temperature_c": self.temperature_c,
     "temperature_f": self.temperature_f
    }
