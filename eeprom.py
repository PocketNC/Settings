# module for interacting with the Pocket NC's EEPROM chip

from smbus import SMBus
import subprocess
import time
import collections
import os

POCKETNC_DIRECTORY = os.environ.get('POCKETNC_DIRECTORY')
eepromReadWPRExecutable = os.path.join(POCKETNC_DIRECTORY, "Settings/eepromReadWPR")

Version = collections.namedtuple("Version", ["major", "minor", "patch"])

class EEPROM:
  def __init__(self, driver="24c64", addr=0x50, bus=2):
    self._driver = driver
    self._addr = addr
    self._bus = bus

# inputs must be sanitized as they are used to construct a shell command string using shell=True
# See this page for more info: https://docs.python.org/2/library/subprocess.html#frequently-used-arguments
    if type(bus) != int:
      raise TypeError("bus must be an integer")

    if type(addr) != int:
      raise TypeError("addr must be an integer")

    supported_drivers = [ "24c64", "24c128", "24c256", "24c512", "24c1024"]
    if driver not in supported_drivers:
      raise ValueError("Unsupported driver. Supported drivers include: %s" % (supported_drivers,))

# Read the entire EEPROM and store in a file
# ensure file is a path, not a malicious string, so don't blindly use user input
# See this page for more info: https://docs.python.org/2/library/subprocess.html#frequently-used-arguments
  def ReadToFile(self, filename):
    try:
      subprocess.check_output("sudo su -c 'echo %s %s > /sys/bus/i2c/devices/i2c-%s/new_device'" % (self._driver,
                                                                                                    hex(self._addr),
                                                                                                    self._bus), shell=True)
      subprocess.check_output("sudo su -c 'cat /sys/bus/i2c/devices/%s-%04x/eeprom > %s'" % (self._bus,
                                                                                            self._addr,
                                                                                            filename), shell=True)
      return 0
    except:
      return -1
    finally:
      try:
        subprocess.check_output("sudo su -c 'echo %s > /sys/bus/i2c/devices/i2c-%s/delete_device'" % (hex(self._addr),
                                                                                                     self._bus), shell=True)
      except:
        return -1

# Write a file to the beginning of the EEPROM
# ensure file is a path, not a malicious string, so don't blindly use user input
# See this page for more info: https://docs.python.org/2/library/subprocess.html#frequently-used-arguments
  def WriteFile(self, filename):
    try:
      subprocess.check_output("sudo su -c 'echo %s %s > /sys/bus/i2c/devices/i2c-%s/new_device'" % (self._driver,
                                                                                                    hex(self._addr),
                                                                                                    self._bus), shell=True)
      subprocess.check_output("sudo su -c 'cat %s > /sys/bus/i2c/devices/%s-%04x/eeprom'" % (filename, 
                                                                                             self._bus,
                                                                                             self._addr), shell=True)
      return 0
    except:
      return -1
    finally:
      try:
        subprocess.check_output("sudo su -c 'echo %s > /sys/bus/i2c/devices/i2c-%s/delete_device'" % (hex(self._addr),
                                                                                                     self._bus), shell=True)
      except:
        return -1

# reg_addr is a two byte register address and num_bytes is the number of bytes to read starting at that address
  def ReadBytes(self, reg_addr, num_bytes):
    b = SMBus(self._bus)

    bytes = []
    for i in range(num_bytes):
      # smbus assumes single byte register addresses, but the write_byte_data method
      # can be used to write the current address pointer by splitting the register
      # address into the most significant and least significant bytes
      b.write_byte_data(self._addr, reg_addr >> 8, reg_addr & 0xff)

      # Once the address is set a single byte can be read.
      # The chip provides more efficient ways to access data,
      # but this seems to be the only way to do it in python
      # without writing a custom C function to do it.
      bytes.append(b.read_byte(self._addr))
      reg_addr += 1
    b.close()

    return bytes

# reg_addr is a two byte register address and data is a list of bytes to write
  def WriteBytes(self, reg_addr, data):
    b = SMBus(self._bus)
    b.write_i2c_block_data(self._addr, reg_addr >> 8, [ reg_addr & 0xff ] + data)
    b.close()

# enables write protection on the EEPROM chip
# writes will no longer work until the write protection is cleared
  def EnableWriteProtection(self):
    b = SMBus(self._bus)
    # 0b10000000 - See page 24 of 24CW64X data sheet, register address of configuration registers
    # 0 - Extra byte of register address, can be anything as 
    #     long as most significant bit in previous value is 1
    # 0b01001110 - See page 21 of 24CW64X data sheet for more information about the 
    #              Write Protection Register         
    b.write_i2c_block_data(self._addr, 0b10000000, [0, 0b01001110])
    b.close()

  def ClearWriteProtection(self):
    b = SMBus(self._bus)
    # 0b10000000 - See page 24 of 24CW64X data sheet, register address of configuration registers
    # 0 - Extra byte of register address, can be anything as 
    #     long as most significant bit in previous value is 1
    # 0b01000000 - See page 21 of 24CW64X data sheet for more information about the 
    #              Write Protection Register         
    b.write_i2c_block_data(self._addr, 0b10000000, [0, 0b01000000])
    b.close()

# Permanently enables write protection on the EEPROM chip
# This is NOT undoable without physically replacing the EEPROM chip with an unlocked one.
  def EnableWriteProtectionAndLockConfigurationRegisters(self):
    b = SMBus(self._bus)
    # 0b10000000 - See page 24 of 24CW64X data sheet, register address of configuration registers
    # 0 - Extra byte of register address, can be anything as 
    #     long as most significant bit in previous value is 1
    # 0b01101111 - See page 21 of 24CW64X data sheet for more information about the 
    #              Write Protection Register         
    b.write_i2c_block_data(self._addr, 0b10000000, [0, 0b01101111])
    b.close()

  def isWriteProtected(self):
    try:
      wpr = int(subprocess.check_output([ eepromReadWPRExecutable ]))

      return (wpr & 0b1110) == 0b1110
    except:
      return False
   
# Returns whether the EEPROM configuration registers have been locked
  def isLocked(self):
    try:
      wpr = int(subprocess.check_output([ eepromReadWPRExecutable ]))

      return (wpr & 0b00000001) == 1
    except:
      return False
    

# During board assembly, the EEPROM is programed with the board revision using semantic versioning
# First byte is the major version
# Next byte is the minor version
# Next byte is the patch version
  def ReadBoardRevision(self):
    bytes = self.ReadBytes(0, 3)

    return Version(bytes[0],
                   bytes[1],
                   bytes[2])


if __name__ == "__main__":
  eeprom = EEPROM()
  print(eeprom.ReadBoardRevision())
#  eeprom.EnableWriteProtection()
#  eeprom.EnableWriteProtectionAndLockConfigurationRegisters()
#  print(eeprom.isLocked())
#  print(eeprom.isWriteProtected())
#  eeprom.ClearWriteProtection()
#  time.sleep(.1)
#  eeprom.WriteBytes(1016, [ ord(c) for c in "This is a string" ])
#  time.sleep(.1)
#  print(eeprom.ReadBytes(1000, 6))

#  eeprom.ReadToFile("/tmp/blah")
#  eeprom.WriteFile("/tmp/test")
