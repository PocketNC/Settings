from transitions import Machine
from enum import Enum, auto

# TODO - get these from configuration
X_MIN = -3.3736
X_MAX = 6.2312 
Y_MIN = -3.6487
Y_MAX = 3.4557
Z_MIN = -6.8746
B_MIN = -135
B_MAX = 45

EPS = .000001
SAFE_Z = 0
SAFE_B = 0
SAFE_X = 1
TIME_ALLOWED_TO_OPEN_OR_CLOSE = 4

FAULT_FAILED_TO_CLOSE = -1
FAULT_FAILED_TO_OPEN = -2

class States(Enum):
  STARTUP = auto()
  OK_TO_HOME = auto()
  NOT_CLOSED_AT_STARTUP = auto()
  CLOSE = auto()
  NOT_CLOSED = auto()
  FAULT = auto()
  NOT_OPENED = auto()
  OK_TO_CLOSE = auto()
  NOT_SAFE_TO_CLOSE = auto()
  OPEN = auto()
  OK_TO_OPEN = auto()
  NOT_SAFE_TO_OPEN = auto()

NEXT = "next"

class SoloToolChangerState(object):
  def __init__(self, h):
    self.h = h
    self.machine = Machine(self, states=States, initial=States.STARTUP, ignore_invalid_triggers=True)

    self.machine.add_transition(NEXT, States.STARTUP, States.OK_TO_HOME, conditions="is_closed_sensor_triggered")
    self.machine.add_transition(NEXT, States.STARTUP, States.NOT_CLOSED_AT_STARTUP, unless="is_closed_sensor_triggered")

    self.machine.add_transition(NEXT, States.OK_TO_HOME, States.NOT_SAFE_TO_OPEN, conditions="is_homed")

    self.machine.add_transition(NEXT, States.OK_TO_OPEN, States.NOT_SAFE_TO_OPEN, unless="is_safe_to_open")
    self.machine.add_transition(NEXT, States.OK_TO_OPEN, States.OPEN, conditions="is_open_requested")
    self.machine.add_transition(NEXT, States.OK_TO_OPEN, States.STARTUP, unless="is_homed")

    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_OPEN, States.OK_TO_OPEN, conditions="is_safe_to_open")
    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_OPEN, States.STARTUP, unless="is_homed")

    self.machine.add_transition(NEXT, States.OPEN, States.OK_TO_CLOSE, conditions="is_opened_sensor_triggered")
    self.machine.add_transition(NEXT, States.OPEN, States.NOT_OPENED, conditions="has_drawer_timed_out")
    self.machine.add_transition(NEXT, States.OPEN, States.STARTUP, unless="is_homed")

    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.NOT_SAFE_TO_CLOSE, unless="is_safe_to_close")
    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.CLOSE, conditions="is_close_requested")
    self.machine.add_transition(NEXT, States.OK_TO_CLOSE, States.STARTUP, unless="is_homed")

    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_CLOSE, States.OK_TO_CLOSE, conditions="is_safe_to_close")
    self.machine.add_transition(NEXT, States.NOT_SAFE_TO_CLOSE, States.STARTUP, unless="is_homed")

    self.machine.add_transition(NEXT, States.CLOSE, States.OK_TO_HOME, conditions="is_closed_sensor_triggered")
    self.machine.add_transition(NEXT, States.CLOSE, States.NOT_CLOSED, conditions="has_drawer_timed_out")

    self.machine.add_transition(NEXT, States.NOT_CLOSED_AT_STARTUP, States.CLOSE, conditions="has_user_indicated_safe_to_close")
    self.machine.add_transition(NEXT, States.NOT_CLOSED_AT_STARTUP, States.OK_TO_HOME, conditions="is_closed_sensor_triggered")

    self.machine.add_transition(NEXT, States.FAULT, States.STARTUP, unless="is_homed")

    self.time_since_open_or_close = 0

  def incrementTime(self, dt):
    self.time_since_open_or_close += dt

  def resetTime(self):
    self.time_since_open_or_close = 0

  def on_enter_NOT_CLOSED_AT_STARTUP(self):
    print("NOT_CLOSED_AT_STARTUP")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0

  def on_enter_STARTUP(self):
    print("STARTUP")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0

  def on_enter_OPEN(self):
    print("OPEN")
    self.resetTime()

    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS # TODO -- pull this out of config?

  def on_enter_CLOSE(self):
    print("CLOSE")
    self.resetTime()

    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS # TODO -- pull this out of config?

  def on_enter_OK_TO_HOME(self):
    print("OK_TO_HOME")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN

  def on_enter_OK_TO_OPEN(self):
    print("OK_TO_OPEN")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN

  def on_enter_NOT_SAFE_TO_OPEN(self):
    print("NOT_SAFE_TO_OPEN")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  True
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = False
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = B_MIN

  def on_enter_OK_TO_CLOSE(self):
    print("OK_TO_CLOSE")
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS # TODO -- pull this out of config?


  def on_enter_NOT_SAFE_TO_CLOSE(self):
    print("NOT_SAFE_TO_CLOSE")
    self.h["state"] = self.state.value
    self.h["open-out"] = True
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = False
    self.h["inhibit-homing"] = True
    self.h["fault"] = False
    self.h["fault-reason"] = 0
    self.h["b-min"] = -EPS # TODO -- pull this out of config?

  def on_enter_NOT_OPENED(self):
    print("Failed to open tool changer drawer")
    self.h["fault-reason"] = FAULT_FAILED_TO_OPEN
    self.to_FAULT()

  def on_enter_NOT_CLOSED(self):
    print("Failed to close tool changer drawer")
    self.h["fault-reason"] = FAULT_FAILED_TO_CLOSE
    self.to_FAULT()

  def on_enter_FAULT():
    print("FAULT")
    self.h["state"] = self.state.value
    self.h["open-out"] = False
    self.h["close-out"] =  False
    self.h["inhibit-feed"] = True
    self.h["inhibit-homing"] = True
    self.h["fault"] = True
    self.h["b-min"] = -EPS # TODO -- pull this out of config?

  @property
  def has_user_indicated_safe_to_close(self):
    return self.h["safe-to-close"]

  @property
  def has_drawer_timed_out(self):
    return (
      self.time_since_open_or_close > TIME_ALLOWED_TO_OPEN_OR_CLOSE and
      not self.is_closed_sensor_triggered and
      not self.is_opened_sensor_triggered
    )

  @property
  def is_open_requested(self):
    return self.h["open-cmd"]

  @property
  def is_close_requested(self):
    return not self.is_open_requested

  @property
  def is_closed_sensor_triggered(self):
    return self.h["closed-sensor"]

  @property
  def is_opened_sensor_triggered(self):
    return self.h["opened-sensor"]
  
  @property
  def is_homed(self):
    return (
      self.h["x-homed"] and 
      self.h["y-homed"] and 
      self.h["z-homed"] and 
      self.h["b-homed"]
    )

  @property
  def is_safe_to_open(self):
    return (
      self.h["x-homed"] and
      self.h["y-homed"] and
      self.h["z-homed"] and
      self.h["b-homed"] and
      (self.h["x-position"] <= SAFE_X+EPS or
       self.h["z-position"] >= SAFE_Z-EPS) and
      self.h["b-position"] >= SAFE_B-EPS
    )

  @property
  def is_safe_to_close(self):
    return self.is_safe_to_open
