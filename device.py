#!/usr/bin/python3

from enum import Enum

class DeviceModel(Enum):
  UNKNOWN = "UNKNOWN"
  BBB = "BBB"
  BBG = "BBG"
  BBAI = "BBAI"

def getProcDeviceModel():
  try:
    with open("/proc/device-tree/model") as deviceModel:
      return deviceModel.read().strip()
  except:
    pass
  return "UNKNOWN"

def getDeviceModel():
  device = getProcDeviceModel()
  if "AI" in device:
    return DeviceModel.BBAI
  elif "Black" in device:
    return DeviceModel.BBB
  elif "Green" in device:
    return DeviceModel.BBG
  else:
    return DeviceModel.UNKNOWN

if __name__ == "__main__":
  print(getDeviceModel().value)
