#!/usr/bin/python3
import os
import time
import sys

POCKETNC_DIRECTORY = "/home/pocketnc/pocketnc"
sys.path.insert(0, os.path.join(POCKETNC_DIRECTORY, "Settings"))

from i2c import bus

MPRLS_I2CADDR = 0x18

def detect():
  detected = False
  try:
    bus.read_byte_data(MPRLS_I2CADDR, 0)
    detected = True
  except:
    pass
  return detected

if __name__ == "__main__":
  print(1 if detect() else 0 )
