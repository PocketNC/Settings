#!/usr/bin/python3

from enum import Enum

class DeviceModel(Enum):
  UNKNOWN = "UNKNOWN"
  BBB = "BBB"
  BBAI = "BBAI"

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

if __name__ == "__main__":
  print(getDeviceModel().value)
