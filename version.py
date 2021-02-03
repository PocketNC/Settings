#!/usr/bin/python3

# version.py
# If run as a script, print the current machine version to stdout. This is for easy use by bash scripts.
# Can also be imported by a python script, in which case the getVersion function will return the machine version
# as a string.

# The version is assumed to be v2revP unless another version is found by checking the following:
# 1) A version file exists in Settings with a single line that has the machine version to use. This can be used to override
#    any other version settings, and is intended for use with the v1 as there is no easy way to differentiate between v2revP 
#    and the v1 programmatically. When we start offering the ability to upgrade the UI of the v1, the version file will need
#    to be set correctly.
# 2) A device exists on the I2C bus (the one that uses P9_19 and P9_20) at address 0x50. If so, the machine is v2revR.
# 3) TODO - Eventually we want to use an EEPROM chip to read the version of the machine. We may move toward treating
#    our boards as capes (in which case a hardware change would be necessary), but we may do our own versioning using
#    the EEPROM chip at address 0x50, which was installed on v2revR.

import sys
from smbus import SMBus
import os
POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"

from enum import Enum

class Versions(Enum):
  V1REVH = "v1revH"
  V2REVP = "v2revP"
  V2REVR = "v2revR"

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

def getVersion():
  version = "v2revP" # default version if we don't find another using the version file or i2c

  try:
    with open(os.path.join(POCKETNC_DIRECTORY, "Settings/version"), 'r') as versionFile:
      version = versionFile.read().strip();
  except:
    device = getDeviceModel()
    if device == DeviceModel.BBAI:
      bus = 3
    elif device == DeviceModel.BBB:
      bus = 2

    b = SMBus(bus)
    try:
      b.read_byte(0x50)
      version = Versions.V2REVR.value
    except:
      pass
    else:
      raise ValueError("Unsupported device model: %s" % getProcDeviceModel())

  return version

def writeVersionFile(version):
  with open(os.path.join(POCKETNC_DIRECTORY, "Settings/version"), 'w') as versionFile:
    versionFile.write(version)
    versionFile.write("\n")

def hasVersionFile():
  try:
    with open(os.path.join(POCKETNC_DIRECTORY, "Settings/version"), 'r') as versionFile:
      return true
  except:
    return false

def clearVersionFile():
  os.remove(os.path.join(POCKETNC_DIRECTORY, "Settings/version"))

if __name__ == "__main__":
  print(getVersion())
