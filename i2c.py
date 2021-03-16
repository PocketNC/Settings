from device import getDeviceModel, DeviceModel
from smbus import SMBus

model = getDeviceModel()

if model == DeviceModel.BBAI:
  busNum = 3
elif model == DeviceModel.BBB:
  busNum = 2

bus = SMBus(busNum)
