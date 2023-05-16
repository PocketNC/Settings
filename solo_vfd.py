import minimalmodbus

COMMAND_REG   = 0x2000
FREQUENCY_REG = 0x2001

STATUS_REG = 0x2100
OUTPUT_VOLTAGE_REG = 0x2106
OUTPUT_CURRENT_REG = 0x2104
POWER_FACTOR_REG = 0x210A
OUTPUT_TORQUE_REG = 0x210B
OUTPUT_POWER_REG = 0x210F
RPM_REG = 0x210C

# bit        543210
CMD_STOP = 0b000001
CMD_RUN  = 0b000010
CMD_FWD  = 0b010000
CMD_REV  = 0b100000

DEBUG = False

class VFD:
  def __init__(self, port):
    self.port = port

    self.max_hz = 599
    self.max_rpm = 17970

    self.instVFD = minimalmodbus.Instrument(self.port, 1, debug=DEBUG)
    self.instVFD.serial.baudrate = 9600
    self.instVFD.serial.bytesize = 8
    self.instVFD.serial.parity = minimalmodbus.serial.PARITY_NONE
    self.instVFD.serial.stopbits = 1
    self.instVFD.serial.timeout = 0.05
    self.instVFD.mode = minimalmodbus.MODE_RTU

    self.instPLC = minimalmodbus.Instrument(self.port, 2, debug=DEBUG)
    self.instPLC.mode = minimalmodbus.MODE_RTU

    self.debug_register = 0x2100

    self.clamped_with_tool = False
    self.clamped_no_tool = False
    self.not_clamped = False

  def set_speed(self, on, speed):
    # TODO: Implement this function to set the VFD speed
    cmd = 0

    if on:
      cmd |= CMD_RUN
    else:
      cmd |= CMD_STOP

    if speed >= 0:
      cmd |= CMD_FWD
    else:
      cmd |= CMD_REV

    if DEBUG:
      print("Command: %s" % cmd)
      print("Frequency: %s" % (min(int(self.max_hz*100), int(abs(speed)*self.max_hz/self.max_rpm)),))

    self.instVFD.write_register(COMMAND_REG, cmd)
    self.instVFD.write_register(FREQUENCY_REG, min(self.max_hz, abs(speed)*self.max_hz/self.max_rpm), 2)

  def set_debug_register(self, register):
    self.debug_register = register

  def get_data(self):
    # TODO: Implement this function to get the VFD speed
    # Get speed

    try:
      clamped_sensors = self.instPLC.read_bits(1025,3)
      self.clamped_with_tool = clamped_sensors[2]
      self.clamped_no_tool = clamped_sensors[1]
      self.unclamped = clamped_sensors[0]

      self.speed_fb = self.instVFD.read_register(RPM_REG)

      voltage = self.instVFD.read_register(OUTPUT_VOLTAGE_REG, 1)
      current = self.instVFD.read_register(OUTPUT_CURRENT_REG, 2)
      power_factor = self.instVFD.read_register(POWER_FACTOR_REG, 1)/100

      self.output_power = voltage*current*power_factor
      self.output_torque = self.instVFD.read_register(OUTPUT_TORQUE_REG, 1)

      code = self.instVFD.read_register(STATUS_REG)
      self.warn_code = code >> 16
      self.error_code = code & 0xFF

      self.debug_value = self.instVFD.read_register(self.debug_register)
      self.modbus_ok = True
    except KeyboardInterrupt:
      raise
    except:
      self.modbus_ok = False
