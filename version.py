#!/usr/bin/python

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
POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"

def getVersion():
  version = "v2revP" # default version if we don't find another using the version file or i2c

  try:
    with open(os.path.join(POCKETNC_DIRECTORY, "Settings/version"), 'r') as versionFile:
      version = versionFile.read().strip();
  except:
    # Adafruit_I2C calls output text to stdout when an error occurs.
    # We only want to know that there was an error. We don't want the error output
    # to stdout as this script outputs only the version of this machine.
    # So, we need to capture stdout when running i2c calls.

    # Capturing class for capturing stdout 
    # taken from https://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
    from cStringIO import StringIO
    import sys

    class Capturing(list):
      def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
      def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

    try:
      from Adafruit_GPIO.I2C import Device

      try:
        i2c = Device(0x50, 2)
        test = i2c.readU8(0)
        # TODO put version information on EEPROM chip.
        version = "v2revR"
      except:
        pass
    except:
      # Older machines have an old version of Adafruit_I2C.
      # Adafruit_I2C was replaced by Adafruit_GPIO on newer
      # machines.
      from Adafruit_I2C import Adafruit_I2C
      i2c = Adafruit_I2C(0x50)

      # TODO put version information on EEPROM chip.
      # An EEPRROM chip is included on the v2revR board at i2c address (0x50)
      # but we aren't currently using it. For now, just checking if we can
      # read from it.
      with Capturing() as output:
        test = i2c.readU8(0)

      if test != -1:
        version = "v2revR"

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
  print getVersion()
