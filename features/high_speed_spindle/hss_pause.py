#!/usr/bin/python3

from transitions import Machine
from enum import Enum, auto
import time
import traceback
import hal
import os
import datetime
import json
import penta_messages

LOW_PRESSURE_CUTOFF = 0.110316

LOW_TEMP_CUTOFF = 1
HIGH_TEMP_CUTOFF = 48

#Value returned by sensor read methods if the read fails
SENSOR_READ_FAIL_VALUE = -999

class States(Enum):
  NORMAL = auto()
  STOP_SPINDLE = auto()
  INHIBITED = auto()
  WITHIN_LIMITS = auto()
  SPIN_UP = auto()
  ABORT = auto()
  REPEAT_ERRORS = auto()

STOP_SPINDLE_DURATION = .1
ABORT_DURATION = .1
REPEAT_ERRORS_DURATION = 1
INHIBIT_DURATION = 1
SPIN_UP_DURATION = 3

# inputs
TEMPERATURE_PIN = "temperature"
PRESSURE_PIN = "pressure"
RUNNING_PIN = "running"
PAUSED_PIN = "paused"
IDLE_PIN = "idle"
SPINDLE_ON_PIN = "spindle-on"
CYCLE_START_PIN = "cycle-start"

# outputs
STATE_PIN = "state"
ABORT_PIN = "abort"
STOP_SPINDLE_PIN = "stop-spindle"
FEED_HOLD_PIN = "feed-hold"
INHIBIT_FEED_PIN = "inhibit-feed"
INHIBIT_SPINDLE_PIN = "inhibit-spindle"
OK_TO_RUN_PIN = "ok-to-run"

NEXT = "next"

USER_MESSAGES_END_POINT = os.environ.get('USER_MESSAGES_END_POINT')
messageClient = penta_messages.Client(USER_MESSAGES_END_POINT)

def send_temperature_high_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "spindle_temperature", 
    "text": "Ambient temperature is above the spindle's safe operating range of 32-104F (0-40C). Pausing spindle and program to let it cool down.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_temperature_low_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "spindle_temperature", 
    "text": "Ambient temperature is below the spindle's safe operating range of 32-104F (0-40C). Pausing spindle and program to let it warm up.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_pressure_low_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "spindle_pressure", 
    "text": "Spindle air supply pressure below minimum 20 PSI (0.138 MPA). Pausing spindle and program.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_repeat_temperature_high_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "spindle_temperature", 
    "text": "Cannot resume until spindle temperature drops below maximum operating value of 104F (40C).",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_repeat_temperature_low_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "spindle_temperature", 
    "text": "Cannot resume until spindle temperature rises above minimum operating value of 32F (0C).",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_repeat_pressure_low_message():
  messageClient.send(json.dumps({ 
    "type": "warning", 
    "kind": "spindle_pressure", 
    "text": "Cannot resume until air supply pressure reaches 20 PSI (0.138 MPA).",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_pressure_not_detected():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_pressure", 
    "text": "Failed to detect air supply pressure sensor. Spindle cannot be turned on.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_temperature_not_detected():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Failed to detect temperature sensor. Spindle cannot be turned on.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

class HSSSensorsState:
  def __init__(self, h):
    self.h = h

    self.machine = Machine(self, states=States, initial=States.NORMAL, ignore_invalid_triggers=True)

    self.machine.add_transition(NEXT, States.NORMAL, States.ABORT, conditions="should_abort_temperature_not_detected", after=send_temperature_not_detected)
    self.machine.add_transition(NEXT, States.NORMAL, States.ABORT, conditions="should_abort_pressure_not_detected", after=send_pressure_not_detected)
    self.machine.add_transition(NEXT, States.NORMAL, States.INHIBITED, conditions="should_machine_be_inhibited_temperature_high", after=send_temperature_high_message)
    self.machine.add_transition(NEXT, States.NORMAL, States.INHIBITED, conditions="should_machine_be_inhibited_temperature_low", after=send_temperature_low_message)
    self.machine.add_transition(NEXT, States.NORMAL, States.INHIBITED, conditions="should_machine_be_inhibited_pressure_low", after=send_pressure_low_message)

    self.machine.add_transition(NEXT, States.INHIBITED, States.ABORT, conditions="temperature_not_detected", after=send_temperature_not_detected)
    self.machine.add_transition(NEXT, States.INHIBITED, States.ABORT, conditions="pressure_not_detected", after=send_pressure_not_detected)
    self.machine.add_transition(NEXT, States.INHIBITED, States.WITHIN_LIMITS, conditions="sensors_within_limits")
    self.machine.add_transition(NEXT, States.INHIBITED, States.STOP_SPINDLE, conditions="machine_is_idle")
    self.machine.add_transition(NEXT, States.INHIBITED, States.REPEAT_ERRORS, conditions="cycle_start_and_temperature_high_and_enough_time", after=send_repeat_temperature_high_message)
    self.machine.add_transition(NEXT, States.INHIBITED, States.REPEAT_ERRORS, conditions="cycle_start_and_temperature_low_and_enough_time", after=send_repeat_temperature_low_message)
    self.machine.add_transition(NEXT, States.INHIBITED, States.REPEAT_ERRORS, conditions="cycle_start_and_pressure_low_and_enough_time", after=send_repeat_pressure_low_message)

    self.machine.add_transition(NEXT, States.STOP_SPINDLE, States.NORMAL, conditions="stopped_spindle_for_enough_time")

    self.machine.add_transition(NEXT, States.REPEAT_ERRORS, States.INHIBITED, conditions="repeated_errors_for_enough_time")

    self.machine.add_transition(NEXT, States.WITHIN_LIMITS, States.ABORT, conditions="temperature_not_detected", after=send_temperature_not_detected)
    self.machine.add_transition(NEXT, States.WITHIN_LIMITS, States.ABORT, conditions="pressure_not_detected", after=send_pressure_not_detected)
    self.machine.add_transition(NEXT, States.WITHIN_LIMITS, States.INHIBITED, conditions="sensors_out_of_limits")
    self.machine.add_transition(NEXT, States.WITHIN_LIMITS, States.SPIN_UP, conditions="machine_is_running")
    self.machine.add_transition(NEXT, States.WITHIN_LIMITS, States.STOP_SPINDLE, conditions="machine_is_idle")

    self.machine.add_transition(NEXT, States.SPIN_UP, States.ABORT, conditions="temperature_not_detected", after=send_temperature_not_detected)
    self.machine.add_transition(NEXT, States.SPIN_UP, States.ABORT, conditions="pressure_not_detected", after=send_pressure_not_detected)
    self.machine.add_transition(NEXT, States.SPIN_UP, States.INHIBITED, conditions="sensors_out_of_limits")
    self.machine.add_transition(NEXT, States.SPIN_UP, States.NORMAL, conditions="spun_up_for_enough_time")

    self.machine.add_transition(NEXT, States.ABORT, States.NORMAL, conditions="aborted_for_enough_time")

  @property
  def stopped_spindle_for_enough_time(self):
    return (time.time() - self.stopped_spindle_at > STOP_SPINDLE_DURATION)

  @property
  def temperature_not_detected(self):
    return self.h[TEMPERATURE_PIN] == SENSOR_READ_FAIL_VALUE

  @property
  def pressure_not_detected(self):
    return self.h[PRESSURE_PIN] == SENSOR_READ_FAIL_VALUE

  @property
  def should_abort_temperature_not_detected(self):
    return self.h[SPINDLE_ON_PIN] and self.h[TEMPERATURE_PIN] == SENSOR_READ_FAIL_VALUE

  @property
  def should_abort_pressure_not_detected(self):
    return self.h[SPINDLE_ON_PIN] and self.h[PRESSURE_PIN] == SENSOR_READ_FAIL_VALUE

  @property
  def repeated_errors_for_enough_time(self):
    return (time.time() - self.repeated_errors_at > REPEAT_ERRORS_DURATION)
    
  @property
  def spun_up_for_enough_time(self):
    return (time.time() - self.spin_up_started_at > SPIN_UP_DURATION)

  @property
  def aborted_for_enough_time(self):
    return (time.time() - self.aborted_at > ABORT_DURATION)

  @property
  def cycle_start_and_temperature_high_and_enough_time(self):
    return self.h[CYCLE_START_PIN] and self.h[TEMPERATURE_PIN] > HIGH_TEMP_CUTOFF and time.time() - self.inhibited_at > INHIBIT_DURATION

  @property
  def cycle_start_and_temperature_low_and_enough_time(self):
    return self.h[CYCLE_START_PIN] and self.h[TEMPERATURE_PIN] < LOW_TEMP_CUTOFF and time.time() - self.inhibited_at > INHIBIT_DURATION

  @property
  def cycle_start_and_pressure_low_and_enough_time(self):
    return self.h[CYCLE_START_PIN] and self.h[PRESSURE_PIN] < LOW_PRESSURE_CUTOFF and time.time() - self.inhibited_at > INHIBIT_DURATION

  @property
  def should_machine_be_inhibited_temperature_high(self):
    return self.h[TEMPERATURE_PIN] > HIGH_TEMP_CUTOFF and self.h[SPINDLE_ON_PIN] and (self.h[RUNNING_PIN] or self.h[PAUSED_PIN])

  @property
  def should_machine_be_inhibited_temperature_low(self):
    return self.h[TEMPERATURE_PIN] < LOW_TEMP_CUTOFF and self.h[SPINDLE_ON_PIN] and (self.h[RUNNING_PIN] or self.h[PAUSED_PIN])

  @property
  def should_machine_be_inhibited_pressure_low(self):
    return self.h[PRESSURE_PIN] < LOW_PRESSURE_CUTOFF and self.h[SPINDLE_ON_PIN] and (self.h[RUNNING_PIN] or self.h[PAUSED_PIN])

  @property
  def machine_is_running(self):
    return self.h[RUNNING_PIN]

  @property
  def machine_is_idle(self):
    return self.h[IDLE_PIN]

  @property
  def sensors_within_limits(self):
    return (
      self.h[TEMPERATURE_PIN] >= LOW_TEMP_CUTOFF and 
      self.h[TEMPERATURE_PIN] <= HIGH_TEMP_CUTOFF and
      self.h[PRESSURE_PIN] >= LOW_PRESSURE_CUTOFF
    )

  @property
  def sensors_out_of_limits(self):
    return not self.sensors_within_limits

  def on_enter_STOP_SPINDLE(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = True
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = False
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = False
    self.stopped_spindle_at = time.time()

  def on_enter_ABORT(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = True
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = TRUE
    self.h[INHIBIT_SPINDLE_PIN] = TRUE
    self.h[OK_TO_RUN_PIN] = False
    self.aborted_at = time.time()

  def on_enter_NORMAL(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = False
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_INHIBITED(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = True
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = False
    self.inhibited_at = time.time()

  def on_enter_REPEAT_ERRORS(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = False
    self.repeated_errors_at = time.time()

  def on_enter_WITHIN_LIMITS(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_SPIN_UP(self):
    self.h[STATE_PIN] = self.state.value
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = True
    self.spin_up_started_at = time.time()

if __name__ == "__main__":
  h = hal.component('hss_pause')
  h.newpin(CYCLE_START_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(RUNNING_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(PAUSED_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(IDLE_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(SPINDLE_ON_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(TEMPERATURE_PIN, hal.HAL_FLOAT, hal.HAL_IN)
  h.newpin(PRESSURE_PIN, hal.HAL_FLOAT, hal.HAL_IN)

  h.newpin(STATE_PIN, hal.HAL_S32, hal.HAL_OUT)

  h.newpin(ABORT_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(STOP_SPINDLE_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(FEED_HOLD_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(INHIBIT_FEED_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(INHIBIT_SPINDLE_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(OK_TO_RUN_PIN, hal.HAL_BIT, hal.HAL_OUT)

  h[STATE_PIN] = States.NORMAL.value
  h[TEMPERATURE_PIN] = SENSOR_READ_FAIL_VALUE
  h[PRESSURE_PIN] = SENSOR_READ_FAIL_VALUE
  h[STOP_SPINDLE_PIN] = False
  h[FEED_HOLD_PIN] = False
  h[INHIBIT_FEED_PIN] = False
  h[INHIBIT_SPINDLE_PIN] = False
  h[OK_TO_RUN_PIN] = True

  state = HSSSensorsState(h)
  h.ready()

  try:
    while True:
      state.next()
      time.sleep(.05)

  except KeyboardInterrupt:
    raise SystemExit
