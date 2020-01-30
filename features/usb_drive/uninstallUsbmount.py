#!/usr/bin/python 

import sys
import subprocess
import re

# In Pocket NC software version 4.3.0 we added the ability to run GCODE stored on a USB drive. 
# This depends on a Debian package called usbmount to detect a USB drive and automount it to the filesystem. 
# If a user needs to roll back their software version to something earlier, then usbmount needs to be removed

def toIntOrString(text):
  try:
    retval = int(text)
  except ValueError:
    retval = text
  return retval

def natural_keys(text):
  return [ toIntOrString(c) for c in re.split('[v.-]', text) ]

v = sys.argv[1]

if natural_keys(v) < natural_keys("v4.3.0"):
  removalCommand = "sudo apt-get --purge -y remove usbmount"    
  p = subprocess.Popen( removalCommand.split(), stderr=subprocess.STDOUT, stdout=subprocess.PIPE )
  p.wait()
  kernelCheckCommand = "uname -r"
  p = subprocess.Popen( kernelCheckCommand.split(), stderr=subprocess.STDOUT, stdout=subprocess.PIPE )
  if '4.19.59' in p.stdout.read():
    removalCommand = "sudo apt-get --purge -y remove lockfile-progs"
    p = subprocess.Popen( removalCommand.split(), stderr=subprocess.STDOUT, stdout=subprocess.PIPE )
    p.wait()
