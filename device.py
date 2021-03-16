from enum import Enum

class DeviceModel(Enum):
  UNKNOWN = -1
  BBB = 0
  BBAI = 1

def getProcDeviceModel():
  with open("/proc/device-tree/model") as deviceModel:
    return deviceModel.read().strip()

def getDeviceModel():
  device = getProcDeviceModel()
  if "AI" in device:
    return DeviceModel.BBAI
  elif "Black" in device:
    return DeviceModel.BBB
  else:
    return DeviceModel.UNKNOWN
