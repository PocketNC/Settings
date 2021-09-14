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
import os
POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')
VERSION_FILE_PATH = os.path.join(POCKETNC_VAR_DIRECTORY, "version")

from device import getProcDeviceModel
from enum import Enum
from i2c import bus

class Versions(Enum):
  V1REVH = "v1revH"
  V2REVP = "v2revP"
  V2REVR = "v2revR"


def getVersion():
  version = "v2revP" # default version if we don't find another using the version file or i2c

  try:
    with open(VERSION_FILE_PATH, 'r') as versionFile:
      version = versionFile.read().strip();
  except:
    try:
      bus.read_byte(0x50)
      version = Versions.V2REVR.value
    except:
      pass

  return version

def writeVersionFile(version):
  with open(VERSION_FILE_PATH, 'w') as versionFile:
    versionFile.write(version)
    versionFile.write("\n")

def hasVersionFile():
  try:
    with open(VERSION_FILE_PATH, 'r') as versionFile:
      return true
  except:
    return false

def clearVersionFile():
  os.remove(VERSION_FILE_PATH)

if __name__ == "__main__":
  print(getVersion())
