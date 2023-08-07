import i2c
from enum import Enum

class Modes(Enum):
  RGBW = 0
  COLOR_WHEEL = 1

class Registers(Enum):
  MODE = 0
  RED = 1
  GREEN = 2
  BLUE = 3
  WHITE = 4
  TIME_MULTIPLIER = 5
  PIXEL_MULTIPLIER = 6
  BRIGHTNESS = 7
  AMPLITUDE = 8
  PULSE = 9

class SoloLEDStrip:
  def __init__(self,deviceAddress=0x33):
    self.bus = i2c.bus
    self.deviceAddress = deviceAddress

  def write(self, register, value):
    if isinstance(register, Enum):
      reg = register.value
    else:
      reg = register

    if isinstance(value, Enum):
      val = value.value
    else:
      val = value

    print(f"Writing {val} to {reg}")
    self.bus.write_byte_data(self.deviceAddress, reg, val)

  def success(self):
    self.write(Registers.MODE, Modes.RGBW)
    self.write(Registers.RED, 0)
    self.write(Registers.GREEN, 255)
    self.write(Registers.BLUE, 0)
    self.write(Registers.WHITE, 0)
    self.write(Registers.TIME_MULTIPLIER, 1)
    self.write(Registers.BRIGHTNESS, 255)
    self.write(Registers.AMPLITUDE, 240)
    self.write(Registers.PULSE, 1)

  def error(self):
    self.write(Registers.MODE, Modes.RGBW)
    self.write(Registers.RED, 255)
    self.write(Registers.GREEN, 0)
    self.write(Registers.BLUE, 0)
    self.write(Registers.WHITE, 0)
    self.write(Registers.TIME_MULTIPLIER, 8)
    self.write(Registers.BRIGHTNESS, 255)
    self.write(Registers.AMPLITUDE, 255)
    self.write(Registers.PULSE, 1)

  def normal(self):
    self.write(Registers.MODE, Modes.RGBW)
    self.write(Registers.RED, 0)
    self.write(Registers.GREEN, 0)
    self.write(Registers.BLUE, 0)
    self.write(Registers.WHITE, 255)
    self.write(Registers.PULSE, 0)

  def party(self):
    self.write(Registers.MODE, Modes.COLOR_WHEEL)
    self.write(Registers.TIME_MULTIPLIER, 30)
    self.write(Registers.PIXEL_MULTIPLIER, 40)
