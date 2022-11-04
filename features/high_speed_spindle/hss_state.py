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

POCKETNC_VAR_DIRECTORY = os.environ.get('POCKETNC_VAR_DIRECTORY')
LAST_SPINDLE_OFF_FILE = os.path.join(POCKETNC_VAR_DIRECTORY, "last-spindle-off-time.txt")
LOW_PRESSURE_CUTOFF = 0.110316

LOW_TEMP_CUTOFF = 1
HIGH_TEMP_CUTOFF = 48

NO_WARM_UP = 0
SHORT_WARM_UP = 1
FULL_WARM_UP = 2

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

  NEEDS_WARM_UP = auto()
  PERFORMING_WARM_UP = auto()

STOP_SPINDLE_DURATION = .1
ABORT_DURATION = .1
REPEAT_ERRORS_DURATION = 1
INHIBIT_DURATION = 1
SPIN_UP_DURATION = 3

# inputs

# Temperature and pressure data from the hss_sensors component. These were split
# out into a separate component for easier debugging/testing.
TEMPERATURE_PIN = "temperature"
PRESSURE_PIN = "pressure"

# Status pins to know the state of the interpreter.
RUNNING_PIN = "running"
PAUSED_PIN = "paused"
IDLE_PIN = "idle"

# The cycle/start pin. Used to trigger repeat errors when the spindle has been inhibited and a program is paused.
# Since we set ok-to-run to False when in the INHIBITED state, a cycle/start signal will do nothing, but we want
# to tell the user why, so we look at this pin in order to do so.
CYCLE_START_PIN = "cycle-start"

# This pin will be true when the spindle is actually on (connect to the spindle enable pin, 
# which electrically triggers the spindle to turn on).
# This is used when checking whether to pause the spindle after it's been determined that
# temperature or pressure sensors are out of limits.
SPINDLE_ON_PIN = "spindle-on"

# This pin will be true when the spindle is commanded to be on by a program or MDI command. 
# Used to abort when a warm up is needed and the spindle is commanded on. Since we don't
# want the spindle to actually turn on first, we respond to the request rather than the
# spindle actually being on.
SPINDLE_COMMANDED_ON_PIN = "spindle-commanded-on" 

# I/O pins

# This pin is set via M150 that is called during the warm up cycle.
# It is reset after transitioning to PERFORMING_WARM_UP.
RUN_WARM_UP_PIN = "run-warm-up"

# This pin is set via M154 that is called when the warm up cycle completes.
# It is reset after transitioning back to NORMAL state.
COMPLETED_WARM_UP_PIN = "completed-warm-up"

# outputs

STATE_PIN = "state"
ABORT_PIN = "abort"
STOP_SPINDLE_PIN = "stop-spindle"
FEED_HOLD_PIN = "feed-hold"
INHIBIT_FEED_PIN = "inhibit-feed"
INHIBIT_SPINDLE_PIN = "inhibit-spindle"
OK_TO_RUN_PIN = "ok-to-run"

WARM_UP_NEEDED_PIN = "warm-up-needed"

NEXT = "next"

USER_MESSAGES_END_POINT = os.environ.get('USER_MESSAGES_END_POINT')
messageClient = penta_messages.Client(USER_MESSAGES_END_POINT)

def send_completed_warm_up_message():
  messageClient.send(json.dumps({ 
    "type": "info", 
    "kind": "warmup_completed", 
    "text": "The spindle warm up process completed.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_warm_up_interrupted_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "warmup_interrupted", 
    "text": "The spindle warm up process was interrupted.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_starting_full_warm_up_message():
  messageClient.send(json.dumps({ 
    "type": "info", 
    "kind": "spindle_warmup", 
    "text": "Spindle off for more than 1 week. Running full warm up routine, approx. 50 minutes.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_starting_short_warm_up_message():
  messageClient.send(json.dumps({ 
    "type": "info", 
    "kind": "spindle_warmup", 
    "text": "Spindle off for more than 12 hours. Running short warmup routine, approx. 10 minutes.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_starting_unrequired_short_warm_up_message():
  messageClient.send(json.dumps({ 
    "type": "info", 
    "kind": "spindle_warmup", 
    "text": "Warm up not required. Running short warmup routine, approx. 10 minutes.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_full_warm_up_needed_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_warmup", 
    "text": "You must run the full spindle warm up sequence (approx. 50 minutes) since it hasn't been turned on in over 1 week.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_short_warm_up_needed_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_warmup", 
    "text": "You must run the short spindle warm up sequence (approx. 10 minutes) since it hasn't been turned on in over 12 hours.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))


def send_warm_up_needed_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Ambient temperature is above the spindle's safe operating range of 32-104F (0-40C). Pausing spindle and program to let it cool down.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_temperature_high_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Ambient temperature is above the spindle's safe operating range of 32-104F (0-40C). Pausing spindle and program to let it cool down.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_temperature_low_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Ambient temperature is below the spindle's safe operating range of 32-104F (0-40C). Pausing spindle and program to let it warm up.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_pressure_low_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_pressure", 
    "text": "Spindle air supply pressure below minimum 20 PSI (0.138 MPA). Pausing spindle and program.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_pressure_low_warm_up_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_pressure", 
    "text": "Spindle air supply pressure below minimum 20 PSI (0.138 MPA). Aborting warm up.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_temperature_low_warm_up_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Ambient temperature is below the spindle's safe operating range of 32-104F (0-40C). Aborting warm up.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_temperature_high_warm_up_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Ambient temperature is above the spindle's safe operating range of 32-104F (0-40C). Aborting warm up.",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_repeat_temperature_high_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Cannot resume until spindle temperature drops below maximum operating value of 104F (40C).",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_repeat_temperature_low_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
    "kind": "spindle_temperature", 
    "text": "Cannot resume until spindle temperature rises above minimum operating value of 32F (0C).",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
  }))

def send_repeat_pressure_low_message():
  messageClient.send(json.dumps({ 
    "type": "error", 
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

class HSSState:
  def __init__(self, h):
    self.h = h

    self.spindleTurnedOff = False
    self.lastSpindleOff = datetime.datetime.strptime(self.readLastSpindleOffFromDisk(), "%Y-%m-%dT%H:%M:%S.%fZ")

    self.machine = Machine(self, states=States, initial=States.NORMAL, ignore_invalid_triggers=True)

    self.machine.add_transition(NEXT, States.NORMAL, States.ABORT, conditions="should_abort_temperature_not_detected", after=send_temperature_not_detected)
    self.machine.add_transition(NEXT, States.NORMAL, States.ABORT, conditions="should_abort_pressure_not_detected", after=send_pressure_not_detected)
    self.machine.add_transition(NEXT, States.NORMAL, States.NEEDS_WARM_UP, conditions="warm_up_needed")
    self.machine.add_transition(NEXT, States.NORMAL, States.PERFORMING_WARM_UP, conditions="should_run_warm_up", after="send_warm_up_message_and_reset_run_warm_up")
    self.machine.add_transition(NEXT, States.NORMAL, States.INHIBITED, conditions="should_machine_be_inhibited_temperature_high", after=send_temperature_high_message)
    self.machine.add_transition(NEXT, States.NORMAL, States.INHIBITED, conditions="should_machine_be_inhibited_temperature_low", after=send_temperature_low_message)
    self.machine.add_transition(NEXT, States.NORMAL, States.INHIBITED, conditions="should_machine_be_inhibited_pressure_low", after=send_pressure_low_message)
    self.machine.add_transition(NEXT, States.NORMAL, States.NORMAL, conditions="spindleTurnedOff", after="recordSpindleOff")

    self.machine.add_transition(NEXT, States.NEEDS_WARM_UP, States.ABORT, conditions="spindle_commanded_on_and_full_warm_up_needed", after=send_full_warm_up_needed_message)
    self.machine.add_transition(NEXT, States.NEEDS_WARM_UP, States.ABORT, conditions="spindle_commanded_on_and_short_warm_up_needed", after=send_short_warm_up_needed_message)
    self.machine.add_transition(NEXT, States.NEEDS_WARM_UP, States.PERFORMING_WARM_UP, conditions="should_run_warm_up", after="send_warm_up_message_and_reset_run_warm_up")

    self.machine.add_transition(NEXT, States.PERFORMING_WARM_UP, States.ABORT, conditions="temperature_not_detected", after=send_temperature_not_detected)
    self.machine.add_transition(NEXT, States.PERFORMING_WARM_UP, States.ABORT, conditions="pressure_not_detected", after=send_pressure_not_detected)
    self.machine.add_transition(NEXT, States.PERFORMING_WARM_UP, States.ABORT, conditions="paused_or_idle", after=send_warm_up_interrupted_message)
    self.machine.add_transition(NEXT, States.PERFORMING_WARM_UP, States.ABORT, conditions="pressure_low", after=send_pressure_low_warm_up_message)
    self.machine.add_transition(NEXT, States.PERFORMING_WARM_UP, States.ABORT, conditions="temperature_low", after=send_temperature_low_warm_up_message)
    self.machine.add_transition(NEXT, States.PERFORMING_WARM_UP, States.ABORT, conditions="temperature_high", after=send_temperature_high_warm_up_message)
    self.machine.add_transition(NEXT, States.PERFORMING_WARM_UP, States.NORMAL, conditions="completed_warm_up", after="send_completed_and_reset")

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

    self.machine.add_transition(NEXT, States.ABORT, States.NEEDS_WARM_UP, conditions="needs_warm_up_and_aborted_for_enough_time")
    self.machine.add_transition(NEXT, States.ABORT, States.NORMAL, conditions="aborted_for_enough_time")

  def send_completed_and_reset(self):
    send_completed_warm_up_message()
    self.recordSpindleOff()
    self.reset_complete_warm_up()

  @property
  def completed_warm_up(self):
    return self.h[COMPLETED_WARM_UP_PIN]

  @property
  def paused_or_idle(self):
    return self.h[PAUSED_PIN] or self.h[IDLE_PIN]

  @property
  def spindle_commanded_on_and_full_warm_up_needed(self):
    return self.h[SPINDLE_COMMANDED_ON_PIN] and self.full_warm_up_needed

  @property
  def spindle_commanded_on_and_short_warm_up_needed(self):
    return self.h[SPINDLE_COMMANDED_ON_PIN] and self.short_warm_up_needed

  def send_warm_up_message_and_reset_run_warm_up(self):
    if self.full_warm_up_needed:
      send_starting_full_warm_up_message()
    elif self.short_warm_up_needed:
      send_starting_short_warm_up_message()
    else:
      send_starting_unrequired_short_warm_up_message()
    self.h[RUN_WARM_UP_PIN] = 0

  def reset_run_warm_up(self):
    self.h[RUN_WARM_UP_PIN] = 0

  def reset_complete_warm_up(self):
    self.h[COMPLETED_WARM_UP_PIN] = 0

  @property
  def should_run_warm_up(self):
    return self.h[RUN_WARM_UP_PIN]

  def readLastSpindleOffFromDisk(self):
    try:
      f = open(LAST_SPINDLE_OFF_FILE, 'r');
      dateString = f.readline().strip()
      f.close();
    except:
      dateString = "2019-01-01T00:00:00.000000Z"

    return dateString

  def recordSpindleOff(self):
    now = datetime.datetime.utcnow()
    self.lastSpindleOff = now

    f = open(LAST_SPINDLE_OFF_FILE, 'w');
    f.write(now.strftime("%Y-%m-%dT%H:%M:%S.%fZ\n"))
    f.close()

  @property
  def warm_up_needed(self):
    return self.h[WARM_UP_NEEDED_PIN] != 0 and not self.h[SPINDLE_ON_PIN] 

  def checkWarmUpStatus(self):
    warmup = 0
    if self.full_warm_up_needed:
      warmup = 2
    elif self.short_warm_up_needed:
      warmup = 1

    self.h[WARM_UP_NEEDED_PIN] = warmup

  @property
  def full_warm_up_needed(self):
    now = datetime.datetime.utcnow()

    totalTime = (now-self.lastSpindleOff).total_seconds()

# 7 days is 604800 seconds
    return totalTime > 604800

  @property
  def short_warm_up_needed(self):
    now = datetime.datetime.utcnow()

    totalTime = (now-self.lastSpindleOff).total_seconds()

# 12 hours is  43200 seconds
    return totalTime > 43200

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
  def needs_warm_up_and_aborted_for_enough_time(self):
    return self.warm_up_needed and (time.time() - self.aborted_at > ABORT_DURATION)

  @property
  def aborted_for_enough_time(self):
    return (time.time() - self.aborted_at > ABORT_DURATION)

  @property
  def temperature_low(self):
    return self.h[TEMPERATURE_PIN] < LOW_TEMP_CUTOFF

  @property
  def temperature_high(self):
    return self.h[TEMPERATURE_PIN] > HIGH_TEMP_CUTOFF

  @property
  def pressure_low(self):
    return self.h[PRESSURE_PIN] < LOW_PRESSURE_CUTOFF

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

  def setSpindleTurnedOff(self, spindleTurnedOff):
    self.spindleTurnedOff = spindleTurnedOff

  def on_enter_NEEDS_WARM_UP(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = False
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_PERFORMING_WARM_UP(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = False
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_STOP_SPINDLE(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
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
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = False
    self.aborted_at = time.time()

  def on_enter_NORMAL(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = False
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_INHIBITED(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = True
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = False
    self.inhibited_at = time.time()

  def on_enter_REPEAT_ERRORS(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = False
    self.repeated_errors_at = time.time()

  def on_enter_WITHIN_LIMITS(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = True
    self.h[OK_TO_RUN_PIN] = True

  def on_enter_SPIN_UP(self):
    self.h[STATE_PIN] = self.state.value
    self.h[ABORT_PIN] = False
    self.h[STOP_SPINDLE_PIN] = False
    self.h[FEED_HOLD_PIN] = False
    self.h[INHIBIT_FEED_PIN] = True
    self.h[INHIBIT_SPINDLE_PIN] = False
    self.h[OK_TO_RUN_PIN] = True
    self.spin_up_started_at = time.time()

if __name__ == "__main__":
  h = hal.component('hss_state')
  h.newpin(CYCLE_START_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(RUNNING_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(PAUSED_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(IDLE_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(SPINDLE_ON_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(SPINDLE_COMMANDED_ON_PIN, hal.HAL_BIT, hal.HAL_IN)
  h.newpin(TEMPERATURE_PIN, hal.HAL_FLOAT, hal.HAL_IN)
  h.newpin(PRESSURE_PIN, hal.HAL_FLOAT, hal.HAL_IN)

  h.newpin(RUN_WARM_UP_PIN, hal.HAL_BIT, hal.HAL_IO)
  h.newpin(COMPLETED_WARM_UP_PIN, hal.HAL_BIT, hal.HAL_IO)

  h.newpin(STATE_PIN, hal.HAL_S32, hal.HAL_OUT)
  h.newpin(WARM_UP_NEEDED_PIN, hal.HAL_FLOAT, hal.HAL_OUT)
  h.newpin(ABORT_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(STOP_SPINDLE_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(FEED_HOLD_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(INHIBIT_FEED_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(INHIBIT_SPINDLE_PIN, hal.HAL_BIT, hal.HAL_OUT)
  h.newpin(OK_TO_RUN_PIN, hal.HAL_BIT, hal.HAL_OUT)

  h[CYCLE_START_PIN] = 0
  h[RUNNING_PIN] = 0
  h[PAUSED_PIN] = 0
  h[IDLE_PIN] = 0
  h[SPINDLE_ON_PIN] = 0
  h[SPINDLE_COMMANDED_ON_PIN] = 0
  h[TEMPERATURE_PIN] = SENSOR_READ_FAIL_VALUE
  h[PRESSURE_PIN] = SENSOR_READ_FAIL_VALUE

  h[RUN_WARM_UP_PIN] = 0
  h[COMPLETED_WARM_UP_PIN] = 0

  h[STATE_PIN] = States.NORMAL.value
  h[WARM_UP_NEEDED_PIN] = NO_WARM_UP
  h[ABORT_PIN] = 0
  h[STOP_SPINDLE_PIN] = False
  h[FEED_HOLD_PIN] = False
  h[INHIBIT_FEED_PIN] = False
  h[INHIBIT_SPINDLE_PIN] = False
  h[OK_TO_RUN_PIN] = True

  state = HSSState(h)
  h.ready()

  lastSpindleOn = False

  try:
    while True:
      state.setSpindleTurnedOff(not h[SPINDLE_ON_PIN] and lastSpindleOn)
      state.checkWarmUpStatus()
      state.next()

      lastSpindleOn = h[SPINDLE_ON_PIN]
      time.sleep(.05)

  except KeyboardInterrupt:
    raise SystemExit
