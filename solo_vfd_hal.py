#!/usr/bin/python3

import solo_vfd
import hal
import time

ENABLED_PIN_NAME = "enabled"
SPINDLE_ON_PIN_NAME = "spindle-on"
SPINDLE_CMD_PIN_NAME = "speed-cmd"

DEBUG_REGISTER_PIN_NAME = "debug-register"

SPEED_FB_PIN_NAME = "speed-fb"
OUTPUT_TORQUE_PIN_NAME = "output-torque"
OUTPUT_POWER_PIN_NAME = "output-power"
OUTPUT_VOLTAGE_PIN_NAME = "output-voltage"
OUTPUT_CURRENT_PIN_NAME = "output-current"
POWER_ANGLE_PIN_NAME = "power-angle"
MODBUS_OK_PIN_NAME = "modbus-ok"
CLAMPED_NO_TOOL_PIN_NAME = "clamped-no-tool"
CLAMPED_WITH_TOOL_PIN_NAME = "clamped-with-tool"
UNCLAMP_PIN_NAME = "unclamped"
WARN_CODE_PIN_NAME = "warn-code"
ERROR_CODE_PIN_NAME = "error-code"
DEBUG_VALUE_PIN_NAME = "debug-value"

def main():
  h = hal.component("solo_vfd")
  speed_inputs = [
    (ENABLED_PIN_NAME, hal.HAL_BIT),
    (SPINDLE_ON_PIN_NAME, hal.HAL_BIT),
    (SPINDLE_CMD_PIN_NAME, hal.HAL_FLOAT),
  ]

  outputs = [ 
    (SPEED_FB_PIN_NAME, hal.HAL_FLOAT),
    (OUTPUT_POWER_PIN_NAME, hal.HAL_FLOAT),
    (OUTPUT_VOLTAGE_PIN_NAME, hal.HAL_FLOAT),
    (OUTPUT_CURRENT_PIN_NAME, hal.HAL_FLOAT),
    (POWER_ANGLE_PIN_NAME, hal.HAL_FLOAT),
    (OUTPUT_TORQUE_PIN_NAME, hal.HAL_FLOAT),
    (MODBUS_OK_PIN_NAME, hal.HAL_BIT),
    (CLAMPED_NO_TOOL_PIN_NAME, hal.HAL_BIT),
    (CLAMPED_WITH_TOOL_PIN_NAME, hal.HAL_BIT),
    (UNCLAMP_PIN_NAME, hal.HAL_BIT),
    (WARN_CODE_PIN_NAME, hal.HAL_S32),
    (ERROR_CODE_PIN_NAME, hal.HAL_S32),
    (DEBUG_VALUE_PIN_NAME, hal.HAL_S32)
  ]

  h.newpin(DEBUG_REGISTER_PIN_NAME, hal.HAL_S32, hal.HAL_IN)

  for (pinName, pinType) in speed_inputs:
    h.newpin(pinName, pinType, hal.HAL_IN)

  for (pinName,pinType) in outputs:
    h.newpin(pinName, pinType, hal.HAL_OUT)

  h[DEBUG_REGISTER_PIN_NAME] = 0x2100
  h.ready()

  vfd = solo_vfd.VFD("/dev/ttyO2")

  lastValues = {}
  for (pinName, pinType) in speed_inputs:
    lastValues[pinName] = h[pinName]

  while True:
    for (pinName, pinType) in speed_inputs:
      if lastValues[pinName] != h[pinName]:
        if not h[ENABLED_PIN_NAME]:
          vfd.set_speed(False, 0)
        else:
          vfd.set_speed(h[SPINDLE_ON_PIN_NAME], h[SPINDLE_CMD_PIN_NAME])

      lastValues[pinName] = h[pinName]

    if h[DEBUG_REGISTER_PIN_NAME] != vfd.debug_register:
      vfd.debug_register = h[DEBUG_REGISTER_PIN_NAME] 

    if h[ENABLED_PIN_NAME]:
      vfd.get_data()

      h[SPEED_FB_PIN_NAME] = vfd.speed_fb
      h[OUTPUT_POWER_PIN_NAME] = vfd.output_power
      h[OUTPUT_CURRENT_PIN_NAME] = vfd.output_current
      h[OUTPUT_VOLTAGE_PIN_NAME] = vfd.output_voltage
      h[POWER_ANGLE_PIN_NAME] = vfd.power_angle
      h[OUTPUT_TORQUE_PIN_NAME] = vfd.output_torque
      h[MODBUS_OK_PIN_NAME] = vfd.modbus_ok
      h[CLAMPED_NO_TOOL_PIN_NAME] = vfd.clamped_no_tool
      h[CLAMPED_WITH_TOOL_PIN_NAME] = vfd.clamped_with_tool
      h[UNCLAMP_PIN_NAME] = vfd.unclamped
      h[WARN_CODE_PIN_NAME] = vfd.warn_code
      h[ERROR_CODE_PIN_NAME] = vfd.error_code
      h[DEBUG_VALUE_PIN_NAME] = vfd.debug_value

    time.sleep(.1)

if __name__ == "__main__":
  main()
