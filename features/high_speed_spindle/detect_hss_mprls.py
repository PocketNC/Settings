#!/usr/bin/python3
import os
import time

MPRLS_I2CADDR = 0x18

def detect():
  # Adafruit_I2C calls output text to stdout when an error occurs.
  # We only want to know that there was an error. We don't want the error output
  # to stdout as this script outputs only the version of this machine.
  # So, we need to capture stdout when running i2c calls.
  # Capturing class for capturing stdout 
  # taken from https://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
  from io import StringIO
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
    i2c = Device(MPRLS_I2CADDR, 2)
  except:
    # Older machines have an old version of Adafruit_I2C.
    # Adafruit_I2C was replaced by Adafruit_GPIO on newer machines.
    from Adafruit_I2C import Adafruit_I2C
    i2c = Adafruit_I2C(MPRLS_I2CADDR, 1)
  
  with Capturing() as output:
    try:
      test = i2c.readU8(0)
      if test != -1:
        return 1
      else:
        return 0
    except:
      return 0

if __name__ == "__main__":
  print(detect())
