from device import getDeviceModel, DeviceModel
from smbus import SMBus
import Adafruit_GPIO.I2C

model = getDeviceModel()

if model == DeviceModel.BBAI:
  busNum = 3
  bus = SMBus(busNum)
elif model == DeviceModel.BBB or model == DeviceModel.BBG:
  busNum = 2
  bus = SMBus(busNum)
else:
  busNum = None
  bus = None

class I2C(Adafruit_GPIO.I2C.Device):
  def __init__(self, address):
    super().__init__(address, busNum)
